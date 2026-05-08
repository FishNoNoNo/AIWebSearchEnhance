from __future__ import annotations

from dataclasses import dataclass

from src.api.models.request import ChatCompletionRequest
from src.api.models.response import SearchMetadata
from src.core.client_manager import ClientManager
from src.core.config_loader import SearchStrategySettings
from src.core.exceptions import InvalidRequestError, SearchEngineError
from src.models.analyzer import SearchAnalyzer
from src.models.organizer import SearchResultOrganizer
from src.pipeline.context_builder import ContextBuilder
from src.search.manager import SearchEngineManager
from src.search.models import SearchResult
from src.utils.metrics import MetricsCollector


@dataclass(slots=True)
class ChatExecutionResult:
    content: str
    model: str
    usage: dict[str, object]
    search_metadata: SearchMetadata


class PipelineExecutor:
    def __init__(
        self,
        *,
        client_manager: ClientManager,
        analyzer: SearchAnalyzer,
        search_manager: SearchEngineManager,
        organizer: SearchResultOrganizer,
        context_builder: ContextBuilder,
        strategy: SearchStrategySettings,
        metrics: MetricsCollector,
    ) -> None:
        self.client_manager = client_manager
        self.analyzer = analyzer
        self.search_manager = search_manager
        self.organizer = organizer
        self.context_builder = context_builder
        self.strategy = strategy
        self.metrics = metrics

    async def execute(self, request: ChatCompletionRequest) -> ChatExecutionResult:
        if not request.client_id:
            raise InvalidRequestError("client_id is required")
        if not request.messages:
            raise InvalidRequestError("messages cannot be empty")
        managed_client = self.client_manager.get_client(request.client_id)
        user_message = self._last_user_message(request)
        metadata = SearchMetadata(searched=False)
        final_messages = [message.model_dump(exclude_none=True) for message in request.messages]

        if not request.search_options.disable_search:
            should_search, queries, reason = await self._decide_search(request, user_message)
            metadata.reason = reason
            if should_search:
                self.metrics.record_search_required()
                results, engine_used = await self._run_searches(request, queries)
                organized = await self.organizer.organize(results)
                final_messages = self.context_builder.build(
                    request.messages,
                    original_user_message=user_message,
                    organized_search_results=organized,
                )
                metadata = SearchMetadata(
                    searched=True,
                    search_queries=queries,
                    engine_used=engine_used,
                    result_count=len(results),
                    sources=[{"title": item.title, "url": item.link} for item in results[:10]],
                    reason=reason,
                )

        generation = await managed_client.client.generate(
            final_messages,
            model=request.model or managed_client.config.model,
            **request.completion_params(),
        )
        return ChatExecutionResult(
            content=generation.content,
            model=request.model or managed_client.config.model,
            usage=generation.usage,
            search_metadata=metadata,
        )

    async def _decide_search(
        self, request: ChatCompletionRequest, user_message: str
    ) -> tuple[bool, list[str], str]:
        options = request.search_options
        if options.custom_queries:
            return True, options.custom_queries[: self.strategy.max_search_queries], "使用自定义搜索词"
        if options.force_search:
            return True, [user_message[:120]], "请求强制搜索"
        analysis = await self.analyzer.analyze(user_message)
        should_search = (
            analysis.need_search
            and analysis.confidence >= self.strategy.min_confidence_threshold
        )
        queries = analysis.search_queries[: self.strategy.max_search_queries]
        if should_search and not queries:
            queries = [user_message[:120]]
        return should_search, queries, analysis.reason

    async def _run_searches(
        self, request: ChatCompletionRequest, queries: list[str]
    ) -> tuple[list[SearchResult], str]:
        max_results = request.search_options.max_results or self.strategy.result_per_query
        engine = request.search_options.engine
        all_results: list[SearchResult] = []
        engines_used: list[str] = []
        errors: dict[str, object] = {}
        for query in queries:
            try:
                response = await self.search_manager.search(
                    query,
                    max_results=max_results,
                    engine=engine,
                )
                all_results.extend(response.results)
                engines_used.append(response.engine_used)
            except SearchEngineError as exc:
                errors[query] = exc.details or exc.message
        deduped = self._dedupe(all_results)
        if not deduped and errors:
            raise SearchEngineError("Search failed for all queries", details=errors)
        return deduped, ",".join(dict.fromkeys(engines_used)) if engines_used else None

    def _last_user_message(self, request: ChatCompletionRequest) -> str:
        for message in reversed(request.messages):
            if message.role == "user":
                return str(message.content)
        raise InvalidRequestError("At least one user message is required")

    def _dedupe(self, results: list[SearchResult]) -> list[SearchResult]:
        seen: set[str] = set()
        output: list[SearchResult] = []
        for item in results:
            key = item.link or item.title
            if key in seen:
                continue
            seen.add(key)
            output.append(item)
        return output
