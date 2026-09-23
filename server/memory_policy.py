"""Conservative model-residency budgets from physical RAM and current pressure.

This module deliberately does not import MLX. Unknown platform data selects the
sequential path rather than guessing that a large machine has free memory.
"""
from dataclasses import dataclass
import re
import subprocess

GIB = 1024 ** 3


@dataclass(frozen=True)
class MemorySnapshot:
    total: int
    available: int
    pressure: str  # normal, warning, critical, unknown


@dataclass(frozen=True)
class MemoryPlan:
    resident: bool
    metal_limit: int
    cache_limit: int
    rss_limit: int
    reason: str


def read_snapshot() -> MemorySnapshot:
    try:
        def read(*args):
            return subprocess.check_output(args, text=True, timeout=2).strip()
        total = int(read('/usr/sbin/sysctl', '-n', 'hw.memsize'))
        pressure = {1:'normal', 2:'warning', 4:'critical'}.get(
            int(read('/usr/sbin/sysctl', '-n', 'kern.memorystatus_vm_pressure_level')), 'unknown')
        vm = read('/usr/bin/vm_stat')
        page_size = int(re.search(r'page size of (\d+) bytes', vm).group(1))
        pages = dict((name, int(count)) for name,count in re.findall(r'^(Pages [^:]+):\s+(\d+)\.', vm, re.M))
        # Inactive memory is reclaimable, not a reservation. Pressure and a
        # separate OS/application reserve keep this estimate conservative.
        available = sum(pages.get(name,0) for name in ['Pages free','Pages inactive','Pages speculative']) * page_size
        return MemorySnapshot(total, min(total, available), pressure)
    except (OSError, ValueError, AttributeError, subprocess.SubprocessError):
        return MemorySnapshot(0, 0, 'unknown')


def choose_plan(snapshot: MemorySnapshot, weights_bytes: int) -> MemoryPlan:
    total, available = snapshot.total, snapshot.available
    if total <= 0 or available < 0 or snapshot.pressure == 'unknown':
        return MemoryPlan(False, 8*GIB, GIB//2, 14*GIB, 'memory-information-unavailable')
    reserve = max(3*GIB, total//8)
    budget = max(0, min(total*3//5, available-reserve))
    # Residency needs model weights AND activation/processor headroom. This
    # threshold must be calibrated against measured peak memory, not file size alone.
    resident_need = weights_bytes + 4*GIB
    resident = snapshot.pressure == 'normal' and budget >= resident_need
    if resident:
        limit = min(budget, resident_need+2*GIB)
        return MemoryPlan(True, limit, min(GIB, limit//12), min(total-reserve,limit+2*GIB), 'sufficient-headroom')
    limit = min(8*GIB, max(4*GIB, total//3))
    return MemoryPlan(False, limit, min(GIB//2, limit//16), min(14*GIB, max(6*GIB,total-reserve)),
        'memory-pressure' if snapshot.pressure != 'normal' else 'insufficient-headroom')


def should_release_resident(snapshot: MemorySnapshot) -> bool:
    """Check pressure between chunks; existing weights are already in available RAM.

    Do not subtract the model estimate again once it is resident. Unknown system
    information is a reason to fall back, never a reason to retain more memory.
    """
    reserve = max(3 * GIB, snapshot.total // 8)
    return snapshot.pressure != "normal" or snapshot.available < reserve


def can_retain_vae(snapshot: MemorySnapshot, active_bytes: int = 0) -> bool:
    """Six GiB projected Metal peak includes the retained VAE and two chunks.

    Reserve scales with physical RAM; unavailable pressure data disables reuse.
    The observed Base32 peak was below this bound on the qualification Mac.
    """
    projected_peak = 6 * GIB
    if snapshot.total <= 0 or not 0 <= active_bytes <= projected_peak:
        return False
    reserve = max(3 * GIB, snapshot.total // 8)
    return (snapshot.pressure == 'normal'
            and snapshot.available >= reserve + projected_peak - active_bytes)


def grouped_window_size(snapshot: MemorySnapshot) -> int:
    """Use two independent chunks only when current headroom permits it."""
    return 2 if can_retain_vae(snapshot) else 1
