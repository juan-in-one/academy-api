async def test_health_ok(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_create_and_get_certification(client):
    payload = {
        "name": "AWS Certified Cloud Practitioner",
        "issuer": "AWS",
        "status": "completed",
        "issued_date": "2025-04-15",
    }
    create_response = await client.post("/certifications", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["name"] == payload["name"]
    assert created["status"] == "completed"

    get_response = await client.get(f"/certifications/{created['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == created["id"]


async def test_get_nonexistent_certification_returns_404(client):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/certifications/{fake_id}")
    assert response.status_code == 404


async def test_create_and_get_goal(client):
    payload = {"name": "Inglés", "target_minutes": 30}
    create_response = await client.post("/goals", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["target_minutes"] == 30
    assert created["active"] is True

    get_response = await client.get(f"/goals/{created['id']}")
    assert get_response.status_code == 200


async def test_today_status_without_check_in(client):
    goal = (await client.post("/goals", json={"name": "Proyectos", "target_minutes": 30})).json()

    response = await client.get(f"/goals/{goal['id']}/today")
    assert response.status_code == 200
    status = response.json()
    assert status["checked_in"] is False
    assert status["goal_met"] is False


async def test_check_in_meets_goal(client):
    goal = (await client.post("/goals", json={"name": "Inglés", "target_minutes": 30})).json()
    today = (await client.get(f"/goals/{goal['id']}/today")).json()["date"]

    check_in_response = await client.post(
        f"/goals/{goal['id']}/check-ins", json={"date": today, "minutes": 45}
    )
    assert check_in_response.status_code == 201

    status = (await client.get(f"/goals/{goal['id']}/today")).json()
    assert status["checked_in"] is True
    assert status["minutes"] == 45
    assert status["goal_met"] is True


async def test_check_in_below_target_not_met(client):
    goal = (await client.post("/goals", json={"name": "Inglés", "target_minutes": 30})).json()
    today = (await client.get(f"/goals/{goal['id']}/today")).json()["date"]

    await client.post(f"/goals/{goal['id']}/check-ins", json={"date": today, "minutes": 10})

    status = (await client.get(f"/goals/{goal['id']}/today")).json()
    assert status["checked_in"] is True
    assert status["goal_met"] is False


async def test_check_in_same_day_updates_instead_of_duplicating(client):
    goal = (await client.post("/goals", json={"name": "Inglés", "target_minutes": 30})).json()
    today = (await client.get(f"/goals/{goal['id']}/today")).json()["date"]

    await client.post(f"/goals/{goal['id']}/check-ins", json={"date": today, "minutes": 10})
    await client.post(f"/goals/{goal['id']}/check-ins", json={"date": today, "minutes": 40})

    check_ins = (await client.get(f"/goals/{goal['id']}/check-ins")).json()
    assert len(check_ins) == 1
    assert check_ins[0]["minutes"] == 40
