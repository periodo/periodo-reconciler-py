import pytest

from periodo_reconciler import (
    RProperty,
    RQuery,
    PeriodoReconciler
)


@pytest.fixture
def p_recon():
    return PeriodoReconciler(host='localhost:8142')
