"use client";

import { useState, useEffect, useCallback } from "react";

const STORAGE_KEY = "markmint_mastered_resources_v1";

export function useResourceMastery() {
  const [masteredIds, setMasteredIds] = useState<Set<string>>(new Set());
  const [isLoaded, setIsLoaded] = useState(false);

  // Load from LocalStorage
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed: string[] = JSON.parse(raw);
        if (Array.isArray(parsed)) {
          setMasteredIds(new Set(parsed));
        }
      }
    } catch {
      // Ignore storage errors
    } finally {
      setIsLoaded(true);
    }
  }, []);

  // Save to LocalStorage
  const save = useCallback((ids: Set<string>) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(Array.from(ids)));
    } catch {
      // Ignore quota/access errors
    }
  }, []);

  const toggleMastered = useCallback((id: string) => {
    setMasteredIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      save(next);
      return next;
    });
  }, [save]);

  const isMastered = useCallback((id: string) => {
    return masteredIds.has(id);
  }, [masteredIds]);

  const getProgress = useCallback((allIds: string[]) => {
    if (!allIds || allIds.length === 0) return { completed: 0, total: 0, percentage: 0 };
    const completed = allIds.filter((id) => masteredIds.has(id)).length;
    const total = allIds.length;
    const percentage = Math.round((completed / total) * 100);
    return { completed, total, percentage };
  }, [masteredIds]);

  return {
    isLoaded,
    masteredIds,
    isMastered,
    toggleMastered,
    getProgress
  };
}
