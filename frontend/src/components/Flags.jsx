import React, { useEffect, useState } from "react";
import { getFlags, updateFlags, addFlags } from "../api";

// Helper to generate stable unique IDs for new flags
let nextId = 1;
function generateId() {
  return `id-${nextId++}`;
}

export default function Flags({ token, project, env }) {
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

  // Editing UI for existing flags
  if (editFlags) {
    return (
      <div>
        <h4>
          Editing Flags for {project} / {env}
        </h4>
        {Object.entries(editFlags).map(([flagKey, flag]) => (
          <div
            key={flagKey}
            style={{ border: "1px solid #ccc", margin: "8px", padding: "8px" }}
          >
            <h5>{flagKey}</h5>
            <label>
              State:{" "}
              <select
                value={flag.state}
                onChange={(e) => handleChange(flagKey, "state", e.target.value)}
              >
                <option value="ENABLED">ENABLED</option>
                <option value="DISABLED">DISABLED</option>
              </select>
            </label>
            <br />
            <label>
              Default Variant:{" "}
              <input
                type="text"
                value={flag.defaultVariant}
                onChange={(e) =>
                  handleChange(flagKey, "defaultVariant", e.target.value)
                }
              />
            </label>
            <br />
            <div>
              Variants:
              {Object.entries(flag.variants).map(([vKey, vVal]) => (
                <div key={vKey}>
                  <input
                    type="text"
                    value={vKey}
                    readOnly
                    style={{ width: "120px", marginRight: "8px" }}
                  />
                  <input
                    type="text"
                    value={String(vVal)}
                    onChange={(e) =>
                      handleVariantsChange(flagKey, vKey, e.target.value)
                    }
                  />
                </div>
              ))}
            </div>
          </div>
        ))}
        <button disabled={saving} onClick={saveChanges}>
          Save
        </button>{" "}
        <button disabled={saving} onClick={() => setEditFlags(null)}>
          Cancel
        </button>
      </div>
    );
  }

  // Adding UI for new flags
  if (addingFlags) {
    return (
      <div>
        <h4>Adding New Flags for {project}</h4>
        {Object.entries(addingFlags).map(([id, flag]) => (
          <div
            key={id}
            style={{ border: "1px solid #ccc", margin: "8px", padding: "8px" }}
          >
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
                style={{ width: "200px" }}
              />
            </h5>
            <label>
              State:{" "}
              <select
                value={flag.state}
                onChange={(e) =>
                  handleChange(id, "state", e.target.value, true)
                }
              >
                <option value="ENABLED">ENABLED</option>
                <option value="DISABLED">DISABLED</option>
              </select>
            </label>
            <br />
            <label>
              Default Variant:{" "}
              <input
                type="text"
                value={flag.defaultVariant}
                onChange={(e) =>
                  handleChange(id, "defaultVariant", e.target.value, true)
                }
              />
            </label>
            <br />
            <div>
              Variants:
              {Object.entries(flag.variants).map(([vKey, vVal]) => (
                <div key={vKey}>
                  <input
                    type="text"
                    value={vKey}
                    readOnly
                    style={{ width: "120px", marginRight: "8px" }}
                  />
                  <input
                    type="text"
                    value={String(vVal)}
                    onChange={(e) =>
                      handleVariantsChange(id, vKey, e.target.value, true)
                    }
                  />
                </div>
              ))}
              <button
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
        >
          Add Another Flag
        </button>
        <br />
        <button disabled={saving} onClick={saveNewFlags}>
          Save New Flags
        </button>{" "}
        <button disabled={saving} onClick={() => setAddingFlags(null)}>
          Cancel
        </button>
      </div>
    );
  }

  // Default view with buttons for edit and add
  return (
    <div>
      <h4>
        Flags for {project} / {env}
      </h4>
      <pre style={{ background: "#000", padding: "10px" }}>
        {JSON.stringify(flags, null, 2)}
      </pre>
      <button onClick={startEditing}>Edit Flags</button>{" "}
      <button onClick={startAdding}>Add Flags</button>
    </div>
  );
}
