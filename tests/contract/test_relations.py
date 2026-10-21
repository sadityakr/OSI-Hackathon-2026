"""Contract for the relation registry: physics relations with equation, validity, source and a self-test."""


def test_registry_has_seed_relations_with_full_provenance():
    from ramanlens.relations import registry
    rels = registry.all_relations()
    assert len(rels) >= 6
    materials = {r.material for r in rels}
    assert {"graphene", "MoS2"} <= materials
    for r in rels:
        assert r.name and r.equation and r.inputs and r.outputs
        assert r.validity, r.name
        assert r.source.doi or r.source.arxiv, r.name
        assert r.source.locator, f"{r.name}: figure, table or equation number in the source"
        assert r.self_tests, f"{r.name}: at least one self-test taken from the source paper"


def test_all_self_tests_pass():
    from ramanlens.relations import registry
    failures = registry.run_self_tests()  # list of (relation name, message); empty when all pass
    assert failures == []


def test_relations_fail_closed_outside_validity():
    from ramanlens.relations import registry
    for r in registry.all_relations():
        out = r.apply(**r.out_of_range_example)
        assert out.applicable is False and out.reason, r.name


def test_registry_is_queryable():
    from ramanlens.relations import registry
    assert registry.find(material="MoS2")
    assert registry.find(input_quantity="delta_E2g_A1g_cm1")
