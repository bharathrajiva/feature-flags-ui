import React, { useEffect, useState } from "react";
import { getFlags, updateFlags, addFlags } from "../api";

// Helper to generate stable unique IDs for new flags
let nextId = 1;
function generateId() {
  return `id-${nextId++}`;
}

export default function Flags({ token, project, env, envs }) {
  const [flags, setFlags] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [editFlags, setEditFlags] = useState(null);
  const [addingFlags, setAddingFlags] = useState(null);

  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!project || !env) return;
    setLoading(true);
    setError(null);
    getFlags(project, env, token)
      .then(setFlags)
      .then(() => {
        setEditFlags(null);
        setAddingFlags(null);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [project, env, token]);

  const hasAlphaBetaCiNightlyEnv =
    typeof env === "string" &&
    (env.endsWith("alpha") ||
      env.endsWith("beta") ||
      env.endsWith("ci") ||
      env.endsWith("nightly"));

  // Handle changes for editing existing flags
  function handleChange(key, field, value, isAdding = false) {
    const setter = isAdding ? setAddingFlags : setEditFlags;
    setter((prev) => ({
      ...prev,
      [key]: {
        ...prev[key],
        [field]: value,
      },
    }));
  }

  // Handle changes for variants
  function handleVariantsChange(flagKey, variantKey, value, isAdding = false) {
    const setter = isAdding ? setAddingFlags : setEditFlags;
    setter((prev) => ({
      ...prev,
      [flagKey]: {
        ...prev[flagKey],
        variants: {
          ...prev[flagKey].variants,
          [variantKey]: value,
        },
      },
    }));
  }

  // Start editing existing flags
  function startEditing() {
    setEditFlags(flags);
  }

  // Start adding new flags - initialize with a template using stable ID and editable flagName
  function startAdding() {
    setAddingFlags({
      [generateId()]: {
        flagName: "new-flag-1",
        state: "ENABLED",
        defaultVariant: "off",
        variants: { on: true, off: false },
      },
    });
  }

  // Save changes for existing flags (updateFlags)
  async function saveChanges() {
    setSaving(true);
    try {
      await updateFlags(project, env, editFlags, token);
      setFlags(editFlags);
      setEditFlags(null);
      alert("Flags updated successfully");
    } catch (e) {
      alert(e.message);
    } finally {
      setSaving(false);
    }
  }

  // Save newly added flags (addFlags)
  async function saveNewFlags() {
    setSaving(true);
    try {
      // Convert addingFlags keyed by id to object keyed by flagName for API
      const payload = Object.values(addingFlags).reduce((acc, flag) => {
        if (flag.flagName.trim()) {
          const { flagName, ...rest } = flag;
          acc[flagName] = rest;
        }
        return acc;
      }, {});

      await addFlags(project, payload, token);

      setFlags((prev) => ({ ...prev, ...payload }));
      setAddingFlags(null);
      alert("New flags added successfully");
    } catch (e) {
      alert(e.message);
    } finally {
      setSaving(false);
    }
  }

  if (!project || !env) return null;
  if (loading) return <p>Loading flags...</p>;
  if (error) return <p style={{ color: "red" }}>{error}</p>;
  if (!flags) return <p>No flags found</p>;

  // Common styles for boxes
  const boxStyle = {
    border: "1px solid #ccc",
    borderRadius: "8px",
    margin: "12px 0",
    padding: "16px",
    boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
    backgroundColor: "#1e1e1e",
  };

  // Common styles for selects to look nicer but same color
  const selectStyle = {
    padding: "6px 10px",
    borderRadius: "6px",
    border: "1px solid #ccc",
    backgroundColor: "#1e1e1e",
    cursor: "pointer",
    fontSize: "1rem",
  };

  // Common styles for inputs
  const inputStyle = {
    padding: "6px 10px",
    borderRadius: "6px",
    border: "1px solid #ccc",
    fontSize: "1rem",
    width: "200px",
    marginBottom: "8px",
  };

  // Common label style
  const labelStyle = {
    display: "block",
    marginBottom: "8px",
    fontWeight: "600",
  };
const variantBoxStyle = {
  backgroundColor: "##1e1e1e",
  border: "1px solid #ddd",
  borderRadius: "6px",
  padding: "12px",
  marginTop: "12px",
};

  // Editing UI for existing flags
  if (editFlags) {
    return (
      <div>
        <h4 style={{ display: "flex", alignItems: "center", gap: "1rem", flexWrap: "wrap" }}>
          Editing Flags for {project} / {env}
          <button disabled={saving} onClick={saveChanges} style={{ padding: "8px 14px", borderRadius: "6px", cursor: saving ? "not-allowed" : "pointer" }}>
            Save
          </button>
          <button disabled={saving} onClick={() => setEditFlags(null)} style={{ padding: "8px 14px", borderRadius: "6px", cursor: saving ? "not-allowed" : "pointer" }}>
            Cancel
          </button>
        </h4>
        {Object.entries(editFlags).map(([flagKey, flag]) => (
          <div key={flagKey} style={boxStyle}>
            <h5 style={{ marginBottom: "12px" }}>{flagKey}</h5>
            <label style={labelStyle}>
              State:{" "}
              <select
                value={flag.state}
                onChange={(e) => handleChange(flagKey, "state", e.target.value)}
                style={selectStyle}
              >
                <option value="ENABLED">ENABLED</option>
                <option value="DISABLED">DISABLED</option>
              </select>
            </label>
            <label style={labelStyle}>
              Default Variant:{" "}
              <input
                type="text"
                value={flag.defaultVariant}
                onChange={(e) => handleChange(flagKey, "defaultVariant", e.target.value)}
                style={inputStyle}
              />
            </label>
<div style={variantBoxStyle}>
  <strong style={{ display: "block", marginBottom: "8px" }}>Variants:</strong>
  {Object.entries(flag.variants).map(([vKey, vVal]) => (
    <div key={vKey} style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "8px" }}>
      <input
        type="text"
        value={vKey}
        readOnly
        style={{ ...inputStyle, width: "140px", cursor: "not-allowed" }}
      />
      <input
        type="text"
        value={String(vVal)}
        onChange={(e) => handleVariantsChange(flagKey, vKey, e.target.value)}
        style={{ ...inputStyle, width: "200px" }}
      />
    </div>
  ))}
</div>

          </div>
        ))}
      </div>
    );
  }

  // Adding UI for new flags
  if (addingFlags) {
    return (
      <div>
        <h4
          style={{
            display: "flex",
            flexWrap: "wrap",
            alignItems: "center",
            gap: "1rem",
            marginBottom: "16px",
          }}
        >
          <span>Adding New Flags for {project}</span>

          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "nowrap" }}>
            <button
              onClick={() =>
                setAddingFlags((prev) => ({
                  ...prev,
                  [generateId()]: {
                    flagName: `new-flag-${Object.keys(prev).length + 1}`,
                    state: "ENABLED",
                    defaultVariant: "off",
                    variants: { on: true, off: false },
                  },
                }))
              }
              style={{ padding: "8px 14px", borderRadius: "6px", cursor: "pointer" }}
            >
              Add Another Flag
            </button>

            <button disabled={saving} onClick={saveNewFlags} style={{ padding: "8px 14px", borderRadius: "6px", cursor: saving ? "not-allowed" : "pointer" }}>
              Save New Flags
            </button>

            <button disabled={saving} onClick={() => setAddingFlags(null)} style={{ padding: "8px 14px", borderRadius: "6px", cursor: saving ? "not-allowed" : "pointer" }}>
              Cancel
            </button>
          </div>
        </h4>

        {Object.entries(addingFlags).map(([id, flag]) => (
          <div key={id} style={boxStyle}>
            <h5>
              <input
                type="text"
                value={flag.flagName}
                onChange={(e) => {
                  const newName = e.target.value;
                  setAddingFlags((prev) => ({
                    ...prev,
                    [id]: {
                      ...prev[id],
                      flagName: newName,
                    },
                  }));
                }}
                style={{ ...inputStyle, width: "220px" }}
              />
            </h5>
            <label style={labelStyle}>
              State:{" "}
              <select
                value={flag.state}
                onChange={(e) => handleChange(id, "state", e.target.value, true)}
                style={selectStyle}
              >
                <option value="ENABLED">ENABLED</option>
                <option value="DISABLED">DISABLED</option>
              </select>
            </label>
            <label style={labelStyle}>
              Default Variant:{" "}
              <input
                type="text"
                value={flag.defaultVariant}
                onChange={(e) => handleChange(id, "defaultVariant", e.target.value, true)}
                style={inputStyle}
              />
            </label>
 <div style={variantBoxStyle}>
  <strong style={{ display: "block", marginBottom: "8px" }}>Variants:</strong>
  {Object.entries(flag.variants).map(([vKey, vVal]) => (
    <div key={vKey} style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "8px" }}>
      <input
        type="text"
        value={vKey}
        readOnly
        style={{ ...inputStyle, width: "140px",  cursor: "not-allowed" }}
      />
      <input
        type="text"
        value={String(vVal)}
        onChange={(e) => handleVariantsChange(id, vKey, e.target.value, true)}
        style={{ ...inputStyle, width: "200px" }}
      />
    </div>
  ))}
  <button
    style={{ padding: "8px 14px", borderRadius: "6px", cursor: saving ? "not-allowed" : "pointer" }}
    onClick={() =>
      setAddingFlags((prev) => ({
        ...prev,
        [id]: {
          ...prev[id],
          variants: {
            ...prev[id].variants,
            ["new-variant"]: "value",
          },
        },
      }))
    }
  >
    Add Variant
  </button>
</div>

          </div>
        ))}
      </div>
    );
  }

  // Default view with buttons for edit and add
  return (
    <div>
      <h4 style={{ display: "flex", alignItems: "center", gap: "1rem", flexWrap: "wrap" }}>
        Flags for {project} / {env}
        <button
          onClick={startEditing}
          style={{
            padding: "8px 14px",
            borderRadius: "6px",
            cursor: "pointer",
            marginLeft: "auto",
          }}
        >
          Edit Flags
        </button>
        {/* Show Add Flags only if at least one env ends with 'alpha' */}
        {hasAlphaBetaCiNightlyEnv && (
          <button
            onClick={startAdding}
            style={{
              padding: "8px 14px",
              borderRadius: "6px",
              cursor: "pointer",
            }}
          >
            Add Flags
          </button>
        )}
      </h4>
      <pre
        style={{
          background: "#000",
          padding: "10px",
          borderRadius: "8px",
          color: "#fff",
          overflowX: "auto",
          maxHeight: "300px",
        }}
      >
        {JSON.stringify(flags, null, 2)}
      </pre>
    </div>
  );
}
