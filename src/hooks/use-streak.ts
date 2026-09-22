"use client";

import { useState, useEffect } from 'react';

export function useStreak() {
  const [streak, setStreak] = useState(0);

  useEffect(() => {
    try {
      const stored = localStorage.getItem('markmint_streak');
      const today = new Date().toISOString().split('T')[0];
      
      if (stored) {
        const { lastDate, count } = JSON.parse(stored);
        if (lastDate === today) {
          // Already logged in today
          setStreak(count);
        } else {
          // Check if yesterday
          const yesterday = new Date();
          yesterday.setDate(yesterday.getDate() - 1);
          const yesterdayStr = yesterday.toISOString().split('T')[0];
          
          if (lastDate === yesterdayStr) {
            // Streak continues
            const newCount = count + 1;
            setStreak(newCount);
            localStorage.setItem('markmint_streak', JSON.stringify({ lastDate: today, count: newCount }));
          } else {
            // Streak broken
            setStreak(1);
            localStorage.setItem('markmint_streak', JSON.stringify({ lastDate: today, count: 1 }));
          }
        }
      } else {
        // First time
        setStreak(1);
        localStorage.setItem('markmint_streak', JSON.stringify({ lastDate: today, count: 1 }));
      }
    } catch (e) {
      setStreak(1);
    }
  }, []);

  return streak;
}
