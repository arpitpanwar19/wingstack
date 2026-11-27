import React, { createContext, useContext, useEffect, useState } from 'react';

const STORAGE_KEY = 'wingstack_agent_workspace';
const EMPTY_WORKSPACE = { profile: null, analysis: null, partnership: null };
const WorkspaceContext = createContext(null);

function readWorkspace() {
  try {
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null');
    return stored && typeof stored === 'object'
      ? { ...EMPTY_WORKSPACE, ...stored }
      : EMPTY_WORKSPACE;
  } catch {
    return EMPTY_WORKSPACE;
  }
}

export function WorkspaceProvider({ children }) {
  const [workspace, setWorkspace] = useState(readWorkspace);

  useEffect(() => {
    if (!workspace.profile && !workspace.analysis && !workspace.partnership) {
      localStorage.removeItem(STORAGE_KEY);
      return;
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(workspace));
  }, [workspace]);

  const saveAnalysis = (form, response) => {
    const resultUser =
      response?.user && typeof response.user === 'object' ? response.user : response;
    const userId =
      response?.user_id ??
      response?.user?.user_id ??
      response?.user?.id ??
      response?.id;

    if (userId === undefined || userId === null || userId === '') {
      throw new Error('Profile analysis did not return a user_id. Check the API response.');
    }

    const profile = {
      name: form.name,
      targetRole: form.target_role,
      intensityMode: form.intensity_mode,
      githubUsername: form.github_username,
      codeforcesHandle: form.codeforces_handle,
      ...resultUser,
      id: userId,
      user_id: userId,
    };

    setWorkspace((current) => ({ ...current, profile, analysis: response }));
    return profile;
  };

  const saveProfile = (updates) => {
    setWorkspace((current) => ({
      ...current,
      profile: { ...(current.profile || {}), ...updates },
    }));
  };

  const savePartnership = (partnership) => {
    setWorkspace((current) => ({ ...current, partnership }));
  };

  const clearWorkspace = () => setWorkspace(EMPTY_WORKSPACE);

  return (
    <WorkspaceContext.Provider
      value={{
        profile: workspace.profile,
        analysis: workspace.analysis,
        partnership: workspace.partnership,
        saveAnalysis,
        saveProfile,
        savePartnership,
        clearWorkspace,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error('useWorkspace must be used inside a WorkspaceProvider.');
  }
  return context;
}
