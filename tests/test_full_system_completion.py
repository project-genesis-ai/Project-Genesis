from genesis.core.config import SimulationConfig
from genesis.core.genesis_runtime import GenesisRuntime
from genesis.core.hardening import audit_state
from genesis.core.scaling import PopulationScaler
from genesis.core.simulation import Simulation
from genesis.core.verification import verify_determinism
from genesis.core.completion import ScaleController
from genesis.orchestration.engineering_loop import EngineeringLoop, EngineeringStage, StageResult


def test_full_runtime_is_deterministic_and_verified():
    def factory():
        return GenesisRuntime(Simulation(config=SimulationConfig(seed=17)))

    left = factory()
    right = factory()
    left.run(2)
    right.run(2)
    assert left.completion.last_signal == right.completion.last_signal
    assert left.simulation.validate().ok
    assert left.verify().checkpoint_digest == right.verify().checkpoint_digest


def test_scale_controller_and_population_partition():
    controller = ScaleController(individual_threshold=10, aggregate_threshold=100, region_size=4)
    assert controller.mode(9) == "individual"
    assert controller.mode(10) == "hybrid"
    assert controller.mode(100) == "aggregate"
    assert controller.active_regions(25) == 3
    assert PopulationScaler(region_capacity=10).partition(25)[-1].population == 5


def test_engineering_gate_is_sequential():
    loop = EngineeringLoop()
    loop.record(StageResult(EngineeringStage.RESEARCH, True))
    loop.record(StageResult(EngineeringStage.ARCHITECTURE, True))
    loop.record(StageResult(EngineeringStage.IMPLEMENTATION, True))
    assert loop.pending()[0] == EngineeringStage.INTEGRATION
    assert not loop.ready_to_ship


def test_hardening_and_determinism():
    def factory():
        return Simulation(config=SimulationConfig(seed=23))

    simulation = factory()
    report = audit_state(simulation)
    assert report.finite_state
    assert report.non_negative_resources
    assert report.non_negative_wallets
    assert report.valid_health
    assert verify_determinism(factory, steps=2)
