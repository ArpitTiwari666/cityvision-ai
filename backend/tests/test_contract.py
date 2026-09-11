def test_trajectory_contract_notes_video_scope():
    # This contract is deliberate: a tracker ID is never presented as a city-wide identity.
    from app.pipeline import InferenceEvent
    event = InferenceEvent(camera_code="CAM-014", observed_at=__import__('datetime').datetime.now(), longitude=75.8, latitude=22.7, track_id="video-local-1")
    assert event.track_id == "video-local-1"
