"""Data-quality gates must not turn challenges or country hints into ranks."""
import importlib.util
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).parents[1]
previous = list(sys.path)
try:
    sys.path.insert(0, str(ROOT / 'scripts/growth'))
    spec = importlib.util.spec_from_file_location('us_observation', ROOT / 'scripts/growth/observe_us_search.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
finally:
    sys.path[:] = previous


@pytest.mark.parametrize('trace', ['', 'loc=US\nloc=US\n', 'loc=USA\n', 'loc=us\n'])
def test_invalid_country_is_not_a_us_observation(trace):
    with pytest.raises(module.StopObservation, match='invalid_country'):
        module.country_hint(trace)


def test_country_hint_does_not_imply_rank_or_browser_market():
    assert module.country_hint('colo=IAD\nloc=US\nip=203.0.113.1\n') == 'US'
    assert module.country_hint('loc=CZ\n') == 'CZ'


@pytest.mark.parametrize('snapshot', ['unusual traffic from your computer network',
                                    'Verify you are not a robot', 'https://www.google.com/sorry/index'])
def test_challenge_stops_before_any_consent_click(snapshot):
    with pytest.raises(module.StopObservation, match='challenge_no_bypass'):
        module.consent_action(snapshot + '\n- button "Reject all" [ref=e7]')


def test_only_one_actual_reject_ref_is_actionable():
    snapshot = '- button "Reject all" [ref=e7]\n- button "Accept all" [ref=e8]'
    assert module.consent_action(snapshot) == 'e7'
    for value in ['Before you continue', '- button "Accept all" [ref=e8]',
                  snapshot + '\n- button "Reject all" [ref=e9]']:
        with pytest.raises(module.StopObservation, match='unresolved_consent'):
            module.consent_action(value)
    assert module.consent_action('- link "Sign in" [ref=e4]\nGoogle Search') is None


@pytest.mark.parametrize('attempt', ['2', '1'])
def test_unapproved_attempt_or_local_context_stops_before_network(monkeypatch, attempt):
    monkeypatch.setenv('GITHUB_RUN_ATTEMPT', attempt)
    monkeypatch.setenv('GITHUB_REPOSITORY', 'jindratilk/voicy' if attempt == '2' else 'fixture/local')
    monkeypatch.setenv('GITHUB_REF', 'refs/tags/voicy-us-search-e19-20261020')
    monkeypatch.setenv('GITHUB_SHA', 'a' * 40)
    with pytest.raises(SystemExit, match='Only the declared one-shot owner tag'):
        module.main()
