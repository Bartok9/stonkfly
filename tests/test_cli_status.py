"""CLI status must fail closed on a corrupt ledger, without Coinbase calls."""

import json
from pathlib import Path

import pytest

from stonkfly.cli import main
from stonkfly.config import Settings
from stonkfly.ledger import Ledger


def test_status_unreadable_ledger(tmp_path, monkeypatch, capsys):
    out = tmp_path / "runs" / "paper"
    out.mkdir(parents=True)
    (out / "ledger.sqlite").write_bytes(b"not a sqlite database")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["stonkfly", "status", "--out", str(out)])
    with pytest.raises(SystemExit, match="Unreadable ledger"):
        main()
    captured = capsys.readouterr()
    assert "Unreadable ledger" in captured.err or captured.out == ""


def test_status_unreadable_meta(tmp_path, monkeypatch):
    out = tmp_path / "runs" / "paper"
    ledger = Ledger(out / "ledger.sqlite", Settings(), "paper")
    ledger.db.execute("UPDATE meta SET value='not-json' WHERE key='mode'")
    ledger.close()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["stonkfly", "status", "--out", str(out)])
    with pytest.raises(SystemExit, match="Unreadable ledger"):
        main()


def test_status_reads_existing_ledger(tmp_path, monkeypatch, capsys):
    out = tmp_path / "runs" / "paper"
    ledger = Ledger(out / "ledger.sqlite", Settings(), "paper")
    ledger.close()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["stonkfly", "status", "--out", str(out)])
    main()
    payload = json.loads(capsys.readouterr().out)
    assert payload["mode"] == "paper"
    assert payload["halted"] is None
    assert payload["cash"] == "100"
