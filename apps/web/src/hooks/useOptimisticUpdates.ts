/**
 * Optimistic Updates Hook
 * Microsoft-level implementation for instant UI feedback with rollback capability
 */

import { useState, useCallback, useRef, useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";

export interface OptimisticUpdate<T> {
  id: string;
  type: 'create' | 'update' | 'delete';
  data: T;
  timestamp: number;
  rollbackData?: T;
  queryKey: string[];
}

export interface OptimisticState<T> {
  pending: OptimisticUpdate<T>[];
  isUpdating: boolean;
  lastUpdate: number | null;
}

export function useOptimisticUpdates() {
  const queryClient = useQueryClient();
  const [updates, setUpdates] = useState<OptimisticUpdate<any>[]>([]);
  const updatesRef = useRef<OptimisticUpdate<any>[]>([]);
  const timeoutRefs = useRef<Map<string, any>>(new Map());

  // Keep ref in sync with state
  updatesRef.current = updates;

  // Cleanup all timeouts on unmount
  useEffect(() => {
    return () => {
      timeoutRefs.current.forEach(timeoutId => clearTimeout(timeoutId));
      timeoutRefs.current.clear();
    };
  }, []);

  // Add optimistic update
  const addOptimisticUpdate = useCallback(<T>(
    id: string,
    type: 'create' | 'update' | 'delete',
    data: T,
    queryKey: string[],
    rollbackData?: T,
    timeout: number = 10000 // 10 seconds default timeout
  ) => {
    const update: OptimisticUpdate<T> = {
      id,
      type,
      data,
      timestamp: Date.now(),
      rollbackData,
      queryKey,
    };

    // Add to pending updates
    setUpdates(prev => [...prev, update]);

    // Update cache optimistically
    const currentCache = queryClient.getQueryData(queryKey);
    let newCache: any;

    switch (type) {
      case 'create':
        newCache = Array.isArray(currentCache)
          ? [...currentCache, data]
          : data;
        break;
      case 'update':
        newCache = Array.isArray(currentCache)
          ? currentCache.map((item: any) =>
            item.id === id ? { ...item, ...data } : item
          )
          : { ...(currentCache as object), ...(data as object) };
        break;
      case 'delete':
        newCache = Array.isArray(currentCache)
          ? currentCache.filter((item: any) => item.id !== id)
          : null;
        break;
    }

    queryClient.setQueryData(queryKey, newCache);
    queryClient.invalidateQueries({
      queryKey,
      refetchType: 'none'
    });

    // Set up timeout for rollback
    const timeoutId = setTimeout(() => {
      rollbackUpdate(id);
    }, timeout);

    timeoutRefs.current.set(id, timeoutId);
  }, [queryClient]);

  // Rollback update
  const rollbackUpdate = useCallback((id: string) => {
    const update = updatesRef.current.find(u => u.id === id);
    if (!update) return;

    // Clear timeout
    const timeoutId = timeoutRefs.current.get(id);
    if (timeoutId) {
      clearTimeout(timeoutId);
      timeoutRefs.current.delete(id);
    }

    // Rollback cache
    if (update.rollbackData !== undefined) {
      const currentCache = queryClient.getQueryData(update.queryKey);
      let rolledBackCache: any;

      switch (update.type) {
        case 'create':
          rolledBackCache = Array.isArray(currentCache)
            ? currentCache.filter((item: any) => item.id !== id)
            : null;
          break;
        case 'update':
          rolledBackCache = Array.isArray(currentCache)
            ? currentCache.map((item: any) =>
              item.id === id ? update.rollbackData : item
            )
            : update.rollbackData;
          break;
        case 'delete':
          rolledBackCache = Array.isArray(currentCache)
            ? [...currentCache, update.rollbackData]
            : update.rollbackData;
          break;
      }

      queryClient.setQueryData(update.queryKey, rolledBackCache);
    }

    // Remove from pending updates
    setUpdates(prev => prev.filter(u => u.id !== id));
  }, [queryClient]);

  // Complete update successfully
  const completeUpdate = useCallback((id: string) => {
    // Clear timeout
    const timeoutId = timeoutRefs.current.get(id);
    if (timeoutId) {
      clearTimeout(timeoutId);
      timeoutRefs.current.delete(id);
    }

    // Remove from pending updates
    setUpdates(prev => prev.filter(u => u.id !== id));

    // Invalidate query to refetch fresh data
    const update = updatesRef.current.find(u => u.id === id);
    if (update) {
      queryClient.invalidateQueries({ queryKey: update.queryKey });
    }
  }, [queryClient]);

  // Check if update is pending
  const isUpdatePending = useCallback((id: string) => {
    return updates.some(u => u.id === id);
  }, [updates]);

  // Get pending updates for query
  const getPendingUpdatesForQuery = useCallback((queryKey: string[]) => {
    return updates.filter(u =>
      JSON.stringify(u.queryKey) === JSON.stringify(queryKey)
    );
  }, [updates]);

  // Clear all pending updates
  const clearAllUpdates = useCallback(() => {
    // Clear all timeouts
    timeoutRefs.current.forEach(timeoutId => clearTimeout(timeoutId));
    timeoutRefs.current.clear();

    // Collect affected query keys before clearing
    const affectedUpdates = updatesRef.current;
    const uniqueQueryKeys = Array.from(new Set(
      affectedUpdates.flatMap(u => u.queryKey.map(k => JSON.stringify(k)))
    ));

    // Clear all updates
    setUpdates([]);

    // Refetch all affected queries
    uniqueQueryKeys.forEach(keyStr => {
      queryClient.invalidateQueries({ queryKey: JSON.parse(keyStr) });
    });
  }, [queryClient]);

  return {
    pending: updates,
    isUpdating: updates.length > 0,
    lastUpdate: updates.length > 0 ? Math.max(...updates.map(u => u.timestamp)) : null,

    actions: {
      addOptimisticUpdate,
      rollbackUpdate,
      completeUpdate,
      clearAllUpdates,
    },

    utils: {
      isUpdatePending,
      getPendingUpdatesForQuery,
    },
  };
}

// Specialized hooks for common operations
export function useOptimisticApplications() {
  const optimistic = useOptimisticUpdates();

  const applyToJob = useCallback((jobId: string, applicationData: any) => {
    optimistic.actions.addOptimisticUpdate(
      `app-${jobId}`,
      'create',
      {
        id: `temp-${Date.now()}`,
        job_id: jobId,
        ...applicationData,
        status: 'APPLYING',
        created_at: new Date().toISOString(),
      },
      ['applications'],
      undefined,
      15000 // 15 seconds for application
    );
  }, [optimistic]);

  const updateApplicationStatus = useCallback((
    applicationId: string,
    status: string,
    additionalData?: any
  ) => {
    optimistic.actions.addOptimisticUpdate(
      applicationId,
      'update',
      {
        status,
        ...additionalData,
        updated_at: new Date().toISOString(),
      },
      ['applications'],
      // Get current data for rollback
      optimistic.utils.getPendingUpdatesForQuery(['applications'])
        .find(u => u.id === applicationId)?.rollbackData
    );
  }, [optimistic]);

  const deleteApplication = useCallback((applicationId: string) => {
    const currentData = optimistic.utils.getPendingUpdatesForQuery(['applications'])
      .find(u => u.id === applicationId)?.rollbackData;

    optimistic.actions.addOptimisticUpdate(
      applicationId,
      'delete',
      {},
      ['applications'],
      currentData
    );
  }, [optimistic]);

  return {
    ...optimistic,
    actions: {
      ...optimistic.actions,
      applyToJob,
      updateApplicationStatus,
      deleteApplication,
    },
  };
}

export function useOptimisticJobs() {
  const optimistic = useOptimisticUpdates();

  const swipeJob = useCallback((
    jobId: string,
    decision: 'ACCEPT' | 'REJECT',
    callbackData?: any
  ) => {
    optimistic.actions.addOptimisticUpdate(
      `swipe-${jobId}`,
      'update',
      {
        user_decision: decision,
        swiped_at: new Date().toISOString(),
        ...callbackData,
      },
      ['jobs'],
      undefined,
      5000 // 5 seconds for swipe
    );
  }, [optimistic]);

  const saveJob = useCallback((jobId: string, notes?: string) => {
    optimistic.actions.addOptimisticUpdate(
      `save-${jobId}`,
      'update',
      {
        is_saved: true,
        saved_notes: notes,
        saved_at: new Date().toISOString(),
      },
      ['jobs'],
      undefined,
      8000 // 8 seconds for save
    );
  }, [optimistic]);

  const hideJob = useCallback((jobId: string) => {
    optimistic.actions.addOptimisticUpdate(
      `hide-${jobId}`,
      'update',
      {
        is_hidden: true,
        hidden_at: new Date().toISOString(),
      },
      ['jobs'],
      undefined,
      6000 // 6 seconds for hide
    );
  }, [optimistic]);

  return {
    ...optimistic,
    actions: {
      ...optimistic.actions,
      swipeJob,
      saveJob,
      hideJob,
    },
  };
}

export function useOptimisticProfile() {
  const optimistic = useOptimisticUpdates();

  const updateProfile = useCallback((updates: any) => {
    optimistic.actions.addOptimisticUpdate(
      'profile',
      'update',
      {
        ...updates,
        updated_at: new Date().toISOString(),
      },
      ['profile'],
      undefined,
      12000 // 12 seconds for profile updates
    );
  }, [optimistic]);

  const uploadResume = useCallback((resumeData: any) => {
    optimistic.actions.addOptimisticUpdate(
      'resume',
      'update',
      {
        resume_url: resumeData.tempUrl,
        upload_status: 'uploading',
        upload_started_at: new Date().toISOString(),
      },
      ['profile'],
      undefined,
      30000 // 30 seconds for upload
    );
  }, [optimistic]);

  const completeResumeUpload = useCallback((finalResumeData: any) => {
    optimistic.actions.addOptimisticUpdate(
      'resume',
      'update',
      {
        ...finalResumeData,
        upload_status: 'completed',
        upload_completed_at: new Date().toISOString(),
      },
      ['profile'],
      undefined,
      5000 // 5 seconds to complete
    );
  }, [optimistic]);

  return {
    ...optimistic,
    actions: {
      ...optimistic.actions,
      updateProfile,
      uploadResume,
      completeResumeUpload,
    },
  };
}

// Batch optimistic updates
export function useBatchOptimisticUpdates() {
  const optimistic = useOptimisticUpdates();

  const batchSwipeJobs = useCallback((
    swipes: Array<{ jobId: string; decision: 'ACCEPT' | 'REJECT' }>
  ) => {
    swipes.forEach(({ jobId, decision }, index) => {
      // Add small delay to prevent race conditions
      setTimeout(() => {
        optimistic.actions.addOptimisticUpdate(
          `batch-swipe-${jobId}`,
          'update',
          {
            user_decision: decision,
            swiped_at: new Date().toISOString(),
            batch_index: index,
          },
          ['jobs'],
          undefined,
          5000
        );
      }, index * 100); // 100ms between each swipe
    });
  }, [optimistic]);

  const batchApplyToJobs = useCallback((
    applications: Array<{ jobId: string; applicationData: any }>
  ) => {
    applications.forEach(({ jobId, applicationData }, index) => {
      setTimeout(() => {
        optimistic.actions.addOptimisticUpdate(
          `batch-apply-${jobId}`,
          'create',
          {
            id: `temp-batch-${Date.now()}-${index}`,
            job_id: jobId,
            ...applicationData,
            status: 'APPLYING',
            created_at: new Date().toISOString(),
            batch_index: index,
          },
          ['applications'],
          undefined,
          20000 // 20 seconds for batch applications
        );
      }, index * 200); // 200ms between each application
    });
  }, [optimistic]);

  return {
    ...optimistic,
    actions: {
      ...optimistic.actions,
      batchSwipeJobs,
      batchApplyToJobs,
    },
  };
}
