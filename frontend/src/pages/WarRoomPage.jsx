import React, { useState } from 'react';
import { AlertTriangle, ArrowUpRight, Github, ShieldAlert, Swords, UsersRound } from 'lucide-react';
import { Link } from 'react-router-dom';
import AppLayout from '../components/AppLayout';
import GlassButton from '../components/GlassButton';
import GlassCard from '../components/GlassCard';
import GlassInput from '../components/GlassInput';
import Notification from '../components/Notification';
import { useWorkspace } from '../context/WorkspaceContext';
import { findPod, simulateMidnight, verifySprintProof } from '../services/api';
import { evaluateKillSwitchProof, getKillSwitchStatus } from "../services/api";

function getPartnershipId(partnership) {
  const data = partnership?.data ?? partnership;
  return data?.partnership_id ?? data?.partnership?.partnership_id;
}

function AgentA5KillSwitchPanel({ defaultPartnershipId = "pod-alpha-1", defaultUserId = "saurav-kumar" }) {
  const [partnershipId, setPartnershipId] = useState(defaultPartnershipId);
  const [userId, setUserId] = useState(defaultUserId);
  const [dailyTask, setDailyTask] = useState("Ship Agent A-5 proof verification & SQLite persistence");
  const [proofText, setProofText] = useState("");
  const [ksStatus, setKsStatus] = useState(null);
  const [ksLoading, setKsLoading] = useState(false);
  const [ksError, setKsError] = useState("");

  const loadStatus = async (pid = partnershipId, uid = userId) => {
    setKsError("");
    try {
      const data = await getKillSwitchStatus(pid.trim() || "pod-alpha-1", uid.trim());
      setKsStatus(data);
    } catch (err) {
      setKsError(err.message || "Unable to fetch kill-switch status");
    }
  };

  useEffect(() => {
    loadStatus(defaultPartnershipId, defaultUserId);
  }, [defaultPartnershipId, defaultUserId]);

  const handleEvaluate = async (streakBroken = false) => {
    setKsLoading(true);
    setKsError("");
    try {
      const data = await evaluateKillSwitchProof({
        partnership_id: partnershipId.trim() || "pod-alpha-1",
        user_id: userId.trim() || "saurav-kumar",
        daily_task: dailyTask.trim() || "Daily War Room Task",
        proof_text: streakBroken ? "[STREAK BROKEN - DEADLINE MISSED]" : proofText,
        streak_broken: streakBroken,
      });
      setKsStatus(data);
      if (!streakBroken && data?.last_verdict === "GENUINE") {
        setProofText("");
      }
    } catch (err) {
      setKsError(err.message || "Agent A-5 evaluation failed");
    } finally {
      setKsLoading(false);
    }
  };

  const isLocked = Boolean(ksStatus?.kill_switch_active);

  return (
    <section
      style={{
        marginTop: "2rem",
        padding: "1.5rem",
        borderRadius: "16px",
        border: isLocked ? "2px solid #ef4444" : "1px solid rgba(255,255,255,0.16)",
        background: isLocked ? "rgba(127, 29, 29, 0.22)" : "rgba(15, 23, 42, 0.72)",
      }}
    >
      <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", gap: "1rem", alignItems: "center" }}>
        <div>
          <h2 style={{ margin: 0, fontSize: "1.25rem" }}>
            Agent A-5: War Room AI Enforcement (The Kill-Switch)
          </h2>
          <p style={{ margin: "0.25rem 0 0", opacity: 0.85, fontSize: "0.92rem" }}>
            Strict AI proof judge, streak enforcement, pod alerts, and SQLite state persistence.
          </p>
        </div>
        <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
          <span
            style={{
              padding: "0.35rem 0.75rem",
              borderRadius: "999px",
              fontWeight: 700,
              fontSize: "0.8rem",
              background: isLocked ? "#dc2626" : "#16a34a",
              color: "#ffffff",
            }}
          >
            {isLocked ? "KILL-SWITCH TRIGGERED" : "ENFORCEMENT ARMED"}
          </span>
          <span style={{ fontWeight: 700 }}>
            Streak: {ksStatus?.streak_days ?? 0}d
          </span>
        </div>
      </div>

      {ksStatus?.last_pod_alert && (
        <div
          style={{
            marginTop: "1rem",
            padding: "0.85rem 1rem",
            borderRadius: "10px",
            background: isLocked ? "rgba(220, 38, 38, 0.18)" : "rgba(34, 197, 94, 0.14)",
            borderLeft: `4px solid ${isLocked ? "#ef4444" : "#22c55e"}`,
          }}
        >
          <strong>Pod Alert ({ksStatus.last_verdict}):</strong> {ksStatus.last_pod_alert}
          <div style={{ fontSize: "0.85rem", opacity: 0.85, marginTop: "0.25rem" }}>
            Judge Reason: {ksStatus.last_reason}
          </div>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "0.75rem", marginTop: "1rem" }}>
        <label style={{ display: "flex", flexDirection: "column", gap: "0.3rem", fontSize: "0.85rem" }}>
          Pod / Partnership ID
          <input
            type="text"
            value={partnershipId}
            onChange={(e) => setPartnershipId(e.target.value)}
            style={{ padding: "0.55rem 0.7rem", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.2)", background: "rgba(0,0,0,0.25)", color: "inherit" }}
          />
        </label>
        <label style={{ display: "flex", flexDirection: "column", gap: "0.3rem", fontSize: "0.85rem" }}>
          Member / User ID
          <input
            type="text"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            style={{ padding: "0.55rem 0.7rem", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.2)", background: "rgba(0,0,0,0.25)", color: "inherit" }}
          />
        </label>
        <label style={{ display: "flex", flexDirection: "column", gap: "0.3rem", fontSize: "0.85rem" }}>
          Assigned Daily Task
          <input
            type="text"
            value={dailyTask}
            onChange={(e) => setDailyTask(e.target.value)}
            style={{ padding: "0.55rem 0.7rem", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.2)", background: "rgba(0,0,0,0.25)", color: "inherit" }}
          />
        </label>
      </div>

      <label style={{ display: "flex", flexDirection: "column", gap: "0.35rem", marginTop: "0.75rem", fontSize: "0.85rem" }}>
        Submit Proof (commit URL, PR link, test output, or detailed task notes)
        <textarea
          rows={3}
          placeholder="e.g., Pushed kill_switch_agent.py and /api/kill-switch/evaluate tests on feat/war-room-kill-switch..."
          value={proofText}
          onChange={(e) => setProofText(e.target.value)}
          style={{ padding: "0.65rem 0.75rem", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.2)", background: "rgba(0,0,0,0.25)", color: "inherit" }}
        />
      </label>

      {ksError && (
        <div style={{ color: "#f87171", marginTop: "0.6rem", fontSize: "0.9rem" }}>
          {ksError}
        </div>
      )}

      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem", marginTop: "0.9rem" }}>
        <button
          type="button"
          disabled={ksLoading}
          onClick={() => handleEvaluate(false)}
          style={{ padding: "0.6rem 1rem", borderRadius: "8px", border: "none", background: "#2563eb", color: "#fff", fontWeight: 600, cursor: "pointer" }}
        >
          {ksLoading ? "Agent A-5 Judging..." : "Submit Proof to Agent A-5"}
        </button>
        <button
          type="button"
          disabled={ksLoading}
          onClick={() => handleEvaluate(true)}
          style={{ padding: "0.6rem 1rem", borderRadius: "8px", border: "none", background: "#dc2626", color: "#fff", fontWeight: 600, cursor: "pointer" }}
        >
          Simulate Streak Break (Kill-Switch)
        </button>
        <button
          type="button"
          disabled={ksLoading}
          onClick={() => loadStatus()}
          style={{ padding: "0.6rem 1rem", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.25)", background: "transparent", color: "inherit", fontWeight: 600, cursor: "pointer" }}
        >
          Refresh SQLite State
        </button>
      </div>

      {Array.isArray(ksStatus?.audit_logs) && ksStatus.audit_logs.length > 0 && (
        <div style={{ marginTop: "1.25rem" }}>
          <h3 style={{ margin: "0 0 0.5rem", fontSize: "1rem" }}>Enforcement Audit Log (SQLite)</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", maxHeight: "220px", overflowY: "auto" }}>
            {ksStatus.audit_logs.map((entry) => (
              <div
                key={entry.id}
                style={{
                  padding: "0.6rem 0.8rem",
                  borderRadius: "8px",
                  background: "rgba(255,255,255,0.04)",
                  fontSize: "0.84rem",
                }}
              >
                <strong>[{entry.verdict}]</strong> {entry.reason} ? <em>Streak: {entry.streak_after}d</em>{" "}
                {entry.kill_switch_active ? "| KILL-SWITCH ON" : "| CLEAR"}
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

function WarRoomPageWithAgentA5(props) {
  return (
    <>
      <WarRoomPage {...props} />
      <AgentA5KillSwitchPanel />
    </>
  );
}

export default WarRoomPageWithAgentA5;
