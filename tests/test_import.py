def test_import():
    import adversary_sim
    assert hasattr(adversary_sim, 'Play')
