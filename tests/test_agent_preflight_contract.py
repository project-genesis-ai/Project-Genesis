from genesis.orchestration.engineering_loop import EngineeringLoop, EngineeringStage, StageResult


def test_preflight_pipeline_cannot_skip_full_testing_before_ci_gate():
    loop = EngineeringLoop()
    loop.record(StageResult(EngineeringStage.RESEARCH, True))
    loop.record(StageResult(EngineeringStage.ARCHITECTURE, True))
    loop.record(StageResult(EngineeringStage.IMPLEMENTATION, True))
    loop.record(StageResult(EngineeringStage.INTEGRATION, True))

    assert EngineeringStage.TESTING in loop.pending()
    assert not loop.can_enter(EngineeringStage.CI_GATE)

    loop.record(StageResult(EngineeringStage.TESTING, True, ("full-suite",)))
    loop.record(StageResult(EngineeringStage.DEBUGGING, True, ("no-failures",)))
    loop.record(StageResult(EngineeringStage.REVIEW, True, ("reviewed",)))
    assert loop.can_enter(EngineeringStage.CI_GATE)


def test_failed_testing_stage_blocks_all_later_stages():
    loop = EngineeringLoop()
    for stage in (
        EngineeringStage.RESEARCH,
        EngineeringStage.ARCHITECTURE,
        EngineeringStage.IMPLEMENTATION,
        EngineeringStage.INTEGRATION,
    ):
        loop.record(StageResult(stage, True))

    try:
        loop.record(StageResult(EngineeringStage.TESTING, False, ("failure",)))
    except ValueError:
        pass
    else:
        raise AssertionError("failed preflight testing must block progression")

    assert not loop.can_enter(EngineeringStage.DEBUGGING)
    assert not loop.can_enter(EngineeringStage.REVIEW)
    assert not loop.can_enter(EngineeringStage.CI_GATE)
