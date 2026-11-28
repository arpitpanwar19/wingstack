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

    const connectors = {
      github_username: form.github_username || resultUser?.connectors?.github_username || '',
      leetcode_username: form.leetcode_username || resultUser?.connectors?.leetcode_username || '',
      codeforces_handle: form.codeforces_handle || resultUser?.connectors?.codeforces_handle || '',
      gfg_handle: form.gfg_handle || resultUser?.connectors?.gfg_handle || '',
      codechef_handle: form.codechef_handle || resultUser?.connectors?.codechef_handle || '',
      atcoder_handle: form.atcoder_handle || resultUser?.connectors?.atcoder_handle || '',
      hackerrank_handle: form.hackerrank_handle || resultUser?.connectors?.hackerrank_handle || '',
    };

    const profile = {
      name: form.name,
      targetRole: form.target_role,
      intensityMode: form.intensity_mode,
      githubUsername: connectors.github_username,
      codeforcesHandle: connectors.codeforces_handle,
      leetcodeUsername: connectors.leetcode_username,
      gfgHandle: connectors.gfg_handle,
      codechefHandle: connectors.codechef_handle,
      atcoderHandle: connectors.atcoder_handle,
      hackerrankHandle: connectors.hackerrank_handle,
      connectors,
      ...resultUser,
      id: userId,
      user_id: userId,
      profile_locked: true,
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
