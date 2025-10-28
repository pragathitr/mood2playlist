from agentic_playlist.agents.critic import Critic
def test_dummy():
    # placeholder to keep pytest happy even if critic behavior changes
    assert Critic(max_calls=1, tracer=None).max_calls == 1
