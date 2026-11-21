import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { getSavedResumes } from '../services/resumeService';

const ACTIVE_RESUME_STORAGE_KEY = 'nexora_active_resume_id';

const ResumeContext = createContext(null);

export function ResumeProvider({ children }) {
  const [activeResumeId, setActiveResumeId] = useState(() => {
    try {
      const stored = localStorage.getItem(ACTIVE_RESUME_STORAGE_KEY);
      return stored || null;
    } catch {
      return null;
    }
  });

  const [activeResume, setActiveResume] = useState(null);
  const [savedResumes, setSavedResumes] = useState([]);
  const [isLoadingResumes, setIsLoadingResumes] = useState(false);
  const [resumeError, setResumeError] = useState(null);

  const selectResume = useCallback((resumeId, resumeData = null) => {
    if (!resumeId) {
      setActiveResumeId(null);
      setActiveResume(null);
      try {
        localStorage.removeItem(ACTIVE_RESUME_STORAGE_KEY);
      } catch {}
      return;
    }

    setActiveResumeId(resumeId);
    setResumeError(null);
    try {
      localStorage.setItem(ACTIVE_RESUME_STORAGE_KEY, resumeId);
    } catch {}

    if (resumeData) {
      setActiveResume(resumeData);
    } else {
      setSavedResumes((current) => {
        const found = current.find((r) => r.id === resumeId);
        if (found) {
          setActiveResume(found);
        }
        return current;
      });
    }
  }, []);

  const clearActiveResume = useCallback(() => {
    setActiveResumeId(null);
    setActiveResume(null);
    setResumeError(null);
    try {
      localStorage.removeItem(ACTIVE_RESUME_STORAGE_KEY);
    } catch {}
  }, []);

  const refreshResumes = useCallback(async () => {
    setIsLoadingResumes(true);
    try {
      const res = await getSavedResumes();
      const list = res?.data || [];
      setSavedResumes(list);

      setActiveResumeId((currentId) => {
        if (!currentId) return null;
        const exists = list.find((r) => r.id === currentId);
        if (exists) {
          setActiveResume(exists);
        }
        return currentId;
      });
    } catch (err) {
      console.warn('Failed to load saved resumes:', err);
    } finally {
      setIsLoadingResumes(false);
    }
  }, []);

  useEffect(() => {
    refreshResumes();
  }, [refreshResumes]);

  const value = {
    activeResumeId,
    activeResume,
    savedResumes,
    isLoadingResumes,
    resumeError,
    setResumeError,
    selectResume,
    clearActiveResume,
    refreshResumes,
  };

  return <ResumeContext.Provider value={value}>{children}</ResumeContext.Provider>;
}

export function useResume() {
  const context = useContext(ResumeContext);
  if (!context) {
    throw new Error('useResume must be used within a ResumeProvider');
  }
  return context;
}
