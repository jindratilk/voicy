from server.memory_policy import GIB, MemorySnapshot, choose_plan


def test_16gb_stays_sequential_with_system_reserve():
    plan = choose_plan(MemorySnapshot(16*GIB, 11*GIB, 'normal'), 6*GIB)
    assert not plan.resident
    assert plan.metal_limit < 8*GIB
    assert plan.rss_limit <= 13*GIB


def test_32gb_with_headroom_can_retain_models():
    plan = choose_plan(MemorySnapshot(32*GIB, 20*GIB, 'normal'), 6*GIB)
    assert plan.resident
    assert 10*GIB <= plan.metal_limit <= 16*GIB


def test_128gb_does_not_allocate_all_ram():
    plan = choose_plan(MemorySnapshot(128*GIB, 100*GIB, 'normal'), 6*GIB)
    assert plan.resident
    assert plan.metal_limit == 12*GIB


def test_busy_128gb_machine_does_not_imply_headroom():
    for pressure, available in [('normal', 12*GIB), ('warning', 100*GIB), ('critical', 100*GIB)]:
        assert not choose_plan(MemorySnapshot(128*GIB, available, pressure), 6*GIB).resident


def test_unknown_information_is_conservative():
    assert not choose_plan(MemorySnapshot(0, 0, 'unknown'), 6*GIB).resident


def test_pressure_transition_releases_existing_models():
    from server.memory_policy import should_release_resident
    assert not should_release_resident(MemorySnapshot(32*GIB, 5*GIB, 'normal'))
    assert should_release_resident(MemorySnapshot(32*GIB, 3*GIB, 'normal'))
    assert should_release_resident(MemorySnapshot(32*GIB, 20*GIB, 'warning'))
    assert should_release_resident(MemorySnapshot(0, 0, 'unknown'))


def test_snapshot_counts_reclaimable_pages_and_reads_pressure(monkeypatch):
    from server.memory_policy import read_snapshot
    responses = iter([str(16*GIB), '2',
        'Mach Virtual Memory Statistics: (page size of 16384 bytes)\n'
        'Pages free: 10.\nPages inactive: 20.\nPages speculative: 3.\nPages wired down: 100.\n'])
    monkeypatch.setattr('server.memory_policy.subprocess.check_output', lambda *a, **kw: next(responses))
    assert read_snapshot() == MemorySnapshot(16*GIB, 33*16384, 'warning')


def test_snapshot_failure_falls_back(monkeypatch):
    from server.memory_policy import read_snapshot
    def missing(*args, **kwargs):
        raise OSError('unavailable')
    monkeypatch.setattr('server.memory_policy.subprocess.check_output', missing)
    assert read_snapshot() == MemorySnapshot(0, 0, 'unknown')


def test_grouped_stage_memory_budgets():
    from server.memory_policy import can_retain_vae, grouped_window_size
    for total in (16, 32, 128):
        reserve = max(3*GIB, total*GIB//8)
        enough = MemorySnapshot(total*GIB, reserve+6*GIB, 'normal')
        assert grouped_window_size(enough) == 2
        assert not can_retain_vae(MemorySnapshot(total*GIB, reserve+6*GIB-1, 'normal'))
        for pressure in ('warning', 'critical', 'unknown'):
            assert grouped_window_size(MemorySnapshot(total*GIB, total*GIB, pressure)) == 1
    assert can_retain_vae(MemorySnapshot(32*GIB, 5*GIB, 'normal'), 5*GIB)
    assert not can_retain_vae(MemorySnapshot(32*GIB, 4*GIB-1, 'normal'), 6*GIB)
    assert not can_retain_vae(MemorySnapshot(0, 0, 'unknown'))
