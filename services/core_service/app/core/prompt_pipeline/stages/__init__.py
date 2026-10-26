"""Стадии модульного конвейера формирования промпта."""

from app.core.prompt_pipeline.stages.base import PipelineStage
from app.core.prompt_pipeline.stages.identity_stage import IdentityStage
from app.core.prompt_pipeline.stages.lorebook_stage import LorebookStage
from app.core.prompt_pipeline.stages.rag_stage import RAGStage
from app.core.prompt_pipeline.stages.scenario_stage import ScenarioStage
from app.core.prompt_pipeline.stages.history_stage import HistoryStage
from app.core.prompt_pipeline.stages.assembler_stage import AssemblerStage


__all__ = [
    "PipelineStage",
    "IdentityStage",
    "LorebookStage",
    "RAGStage",
    "ScenarioStage",
    "HistoryStage",
    "AssemblerStage",
]
