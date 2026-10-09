"""Use case interfaces and protocols.

This module defines the core interfaces and protocols for use cases
in the wallet service. It provides generic type-safe
contracts that all use case implementations must follow.
"""

from typing import Protocol, TypeVar


__all__ = ('IUseCase',)


TInput = TypeVar('TInput', contravariant=True)
TOutput = TypeVar('TOutput', covariant=True)


class IUseCase[TInput, TOutput](Protocol):
    """
    Generic use case protocol following Clean Architecture principles.

    A use case represents a single business operation or workflow that can be
    executed with specific input and produces a predictable output.

    Type Parameters:
        TInput: The input data type for the use case
        TOutput: The output data type returned by the use case
    """

    async def __call__(
        self,
        request: TInput,
    ) -> TOutput:
        """
        Executes the use case with the provided input.

        This method implements the core business logic for a specific operation.
        It should be idempotent and handle all business rules and validations.

        Args:
            input: The input data required to execute the use case

        Returns:
            The result of the use case execution
        """
