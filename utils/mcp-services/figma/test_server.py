import os
import httpx
import pytest
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)


def test_health():
    r = client.get('/health')
    assert r.status_code == 200
    body = r.json()
    assert body['status'] == 'healthy'
    assert 'functions' in body


def test_functions_list():
    r = client.get('/functions')
    assert r.status_code == 200
    funcs = r.json()['functions']
    for expected in ['hello_world', 'process_data', 'get_file', 'get_nodes', 'get_images', 'get_comments']:
        assert expected in funcs


def test_execute_hello_world():
    r = client.post('/execute', json={'function_name': 'hello_world', 'parameters': {}})
    assert r.status_code == 200
    body = r.json()
    assert body['success'] is True
    assert "Hello from figma MCP Server!" in body['result']


async def fake_get(self, url, headers=None, params=None, timeout=None):
    class FakeResp:
        status_code = 200

        def json(self_inner):
            return {"fake": True, "url": url, "params": params}

        text = '{"fake": true}'

    return FakeResp()


def test_execute_get_file(monkeypatch):
    monkeypatch.setenv('FIGMA_TOKEN', 'DUMMY_TOKEN')
    monkeypatch.setattr(httpx.AsyncClient, 'get', fake_get)
    r = client.post('/execute', json={'function_name': 'get_file', 'parameters': {'file_id': 'ABC123'}})
    assert r.status_code == 200
    body = r.json()
    assert body['success'] is True
    assert body['result']['fake'] is True
    assert 'ABC123' in body['result']['url']
