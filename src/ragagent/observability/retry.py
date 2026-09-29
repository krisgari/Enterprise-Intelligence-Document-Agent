"""
Shared retry/backoff policy for calls to external services — the Claude
API and MCP servers — that fail transiently: a rate limit, a momentary
network blip, a provider 5xx. These are worth retrying. A 400 for a
malformed request, or an authentication error, is not — retrying that
just burns time and hides a real bug behind a slow failure. So these
decorators only retry specific, known-transient exception types rather
than "anything that raises."
"""
import logging

import anthropic
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger("ragagent.retry")

RETRYABLE_ANTHROPIC_ERRORS = (
    anthropic.APIConnectionError,
    anthropic.APITimeoutError,
    anthropic.RateLimitError,
    anthropic.InternalServerError,
)

# Up to 3 attempts, exponential backoff starting at 1s and capped at 10s
# (1s, 2s, 4s ... capped) — enough to ride out a brief blip without
# turning a real outage into a long hang.
llm_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(RETRYABLE_ANTHROPIC_ERRORS),
    reraise=True,
    before_sleep=before_sleep_log(logger, logging.WARNING),
)

# MCP servers run as local subprocesses (stdio transport) here, so
# failures look like connection/IO errors rather than HTTP errors.
mcp_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, OSError)),
    reraise=True,
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
