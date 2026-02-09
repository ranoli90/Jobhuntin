/**
 * Team Management Hook
 * Microsoft-level implementation for team collaboration and seat management
 */

import { useState, useCallback, useEffect } from "react";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import { apiPost, apiGet, apiPatch } from "../lib/api";
import { useProfile } from "./useProfile";

// Add apiDelete function since it's not in the main API file
async function apiDelete(path: string): Promise<any> {
  const response = await fetch(`${import.meta.env.VITE_API_URL}/${path}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('supabase_token')}`,
    },
  });
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  
  return response.json();
}

export interface TeamMember {
  id: string;
  email: string;
  full_name: string;
  role: "admin" | "member" | "viewer";
  status: "active" | "pending" | "inactive";
  invited_at: string;
  joined_at?: string;
  last_active?: string;
  applications_count: number;
  success_rate: number;
  avatar_url?: string;
  permissions: TeamPermissions;
}

export interface TeamPermissions {
  can_view_jobs: boolean;
  can_view_applications: boolean;
  can_manage_applications: boolean;
  can_view_analytics: boolean;
  can_manage_team: boolean;
  can_manage_billing: boolean;
  can_manage_settings: boolean;
}

export interface TeamInvitation {
  id: string;
  email: string;
  role: "admin" | "member" | "viewer";
  invited_by: string;
  created_at: string;
  expires_at: string;
  status: "pending" | "accepted" | "expired" | "revoked";
}

export interface TeamSettings {
  team_name: string;
  team_description?: string;
  default_permissions: TeamPermissions;
  require_approval_for_applications: boolean;
  max_members: number;
  auto_share_job_matches: boolean;
  notification_settings: TeamNotificationSettings;
}

export interface TeamNotificationSettings {
  new_application: boolean;
  application_status_change: boolean;
  team_member_joined: boolean;
  team_member_left: boolean;
  billing_alerts: boolean;
  weekly_summary: boolean;
}

export interface TeamAnalytics {
  total_members: number;
  active_members: number;
  total_applications: number;
  success_rate: number;
  average_response_time: number;
  top_performer: TeamMember | null;
  activity_by_member: Array<{
    member_id: string;
    member_name: string;
    applications: number;
    success_rate: number;
  }>;
  monthly_trends: Array<{
    month: string;
    applications: number;
    successes: number;
  }>;
}

interface TeamState {
  isLoading: boolean;
  isInviting: boolean;
  isUpdatingRole: boolean;
  selectedMember: TeamMember | null;
  invitationModalOpen: boolean;
}

export function useTeamManagement() {
  const queryClient = useQueryClient();
  const { profile } = useProfile();
  const [teamState, setTeamState] = useState<TeamState>({
    isLoading: false,
    isInviting: false,
    isUpdatingRole: false,
    selectedMember: null,
    invitationModalOpen: false,
  });

  // Fetch team members
  const {
    data: teamMembers = [],
    isLoading: membersLoading,
    error: membersError,
    refetch: refetchMembers,
  } = useQuery({
    queryKey: ["team-members"],
    queryFn: async () => {
      return await apiGet<TeamMember[]>("team/members");
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
  });

  // Fetch pending invitations
  const {
    data: invitations = [],
    isLoading: invitationsLoading,
    refetch: refetchInvitations,
  } = useQuery({
    queryKey: ["team-invitations"],
    queryFn: async () => {
      return await apiGet<TeamInvitation[]>("team/invitations");
    },
    staleTime: 1 * 60 * 1000, // 1 minute
  });

  // Fetch team settings
  const {
    data: teamSettings,
    isLoading: settingsLoading,
    refetch: refetchSettings,
  } = useQuery({
    queryKey: ["team-settings"],
    queryFn: async () => {
      return await apiGet<TeamSettings>("team/settings");
    },
    staleTime: 10 * 60 * 1000, // 10 minutes
  });

  // Fetch team analytics
  const {
    data: teamAnalytics,
    isLoading: analyticsLoading,
  } = useQuery({
    queryKey: ["team-analytics"],
    queryFn: async () => {
      return await apiGet<TeamAnalytics>("team/analytics");
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Invite team member mutation
  const inviteMemberMutation = useMutation({
    mutationFn: async ({ email, role }: { email: string; role: "admin" | "member" | "viewer" }) => {
      setTeamState(prev => ({ ...prev, isInviting: true }));
      
      const result = await apiPost<TeamInvitation>("team/invite", {
        email,
        role,
        message: `You've been invited to join our team on JobHuntin!`,
      });

      return result;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["team-invitations"] });
      setTeamState(prev => ({ ...prev, invitationModalOpen: false }));
    },
    onError: (error) => {
      console.error("Failed to invite team member:", error);
    },
    onSettled: () => {
      setTeamState(prev => ({ ...prev, isInviting: false }));
    },
  });

  // Update member role mutation
  const updateRoleMutation = useMutation({
    mutationFn: async ({ memberId, role }: { memberId: string; role: "admin" | "member" | "viewer" }) => {
      setTeamState(prev => ({ ...prev, isUpdatingRole: true }));
      
      return await apiPatch<TeamMember>(`team/members/${memberId}`, { role });
    },
    onSuccess: (updatedMember) => {
      queryClient.setQueryData(
        ["team-members"],
        (oldMembers: TeamMember[] | undefined) => 
          oldMembers?.map(member => 
            member.id === updatedMember.id ? updatedMember : member
          )
      );
    },
    onError: (error) => {
      console.error("Failed to update member role:", error);
    },
    onSettled: () => {
      setTeamState(prev => ({ ...prev, isUpdatingRole: false }));
    },
  });

  // Remove team member mutation
  const removeMemberMutation = useMutation({
    mutationFn: async (memberId: string) => {
      return await apiDelete(`team/members/${memberId}`);
    },
    onSuccess: (_, memberId) => {
      queryClient.setQueryData(
        ["team-members"],
        (oldMembers: TeamMember[] | undefined) => 
          oldMembers?.filter(member => member.id !== memberId)
      );
    },
    onError: (error) => {
      console.error("Failed to remove team member:", error);
    },
  });

  // Revoke invitation mutation
  const revokeInvitationMutation = useMutation({
    mutationFn: async (invitationId: string) => {
      return await apiPost(`team/invitations/${invitationId}/revoke`);
    },
    onSuccess: (_, invitationId) => {
      queryClient.setQueryData(
        ["team-invitations"],
        (oldInvitations: TeamInvitation[] | undefined) => 
          oldInvitations?.filter(inv => inv.id !== invitationId)
      );
    },
    onError: (error) => {
      console.error("Failed to revoke invitation:", error);
    },
  });

  // Update team settings mutation
  const updateSettingsMutation = useMutation({
    mutationFn: async (settings: Partial<TeamSettings>) => {
      return await apiPatch<TeamSettings>("team/settings", settings);
    },
    onSuccess: (updatedSettings) => {
      queryClient.setQueryData(["team-settings"], updatedSettings);
    },
    onError: (error) => {
      console.error("Failed to update team settings:", error);
    },
  });

  // Invite team member
  const inviteMember = useCallback(async (email: string, role: "admin" | "member" | "viewer") => {
    if (!email || !role) {
      throw new Error("Email and role are required");
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      throw new Error("Invalid email address");
    }

    await inviteMemberMutation.mutateAsync({ email, role });
  }, [inviteMemberMutation]);

  // Update member role
  const updateMemberRole = useCallback(async (memberId: string, role: "admin" | "member" | "viewer") => {
    await updateRoleMutation.mutateAsync({ memberId, role });
  }, [updateRoleMutation]);

  // Remove team member
  const removeTeamMember = useCallback(async (memberId: string) => {
    if (window.confirm("Are you sure you want to remove this team member? This action cannot be undone.")) {
      await removeMemberMutation.mutateAsync(memberId);
    }
  }, [removeMemberMutation]);

  // Revoke invitation
  const revokeInvitation = useCallback(async (invitationId: string) => {
    await revokeInvitationMutation.mutateAsync(invitationId);
  }, [revokeInvitationMutation]);

  // Update team settings
  const updateTeamSettings = useCallback(async (settings: Partial<TeamSettings>) => {
    await updateSettingsMutation.mutateAsync(settings);
  }, [updateSettingsMutation]);

  // Get member by ID
  const getMemberById = useCallback((memberId: string): TeamMember | undefined => {
    return teamMembers.find(member => member.id === memberId);
  }, [teamMembers]);

  // Get active members only
  const getActiveMembers = useCallback((): TeamMember[] => {
    return teamMembers.filter(member => member.status === "active");
  }, [teamMembers]);

  // Get members by role
  const getMembersByRole = useCallback((role: "admin" | "member" | "viewer"): TeamMember[] => {
    return teamMembers.filter(member => member.role === role);
  }, [teamMembers]);

  // Check if user can perform action
  const canPerformAction = useCallback((action: keyof TeamPermissions, memberRole?: "admin" | "member" | "viewer"): boolean => {
    const role = memberRole || "member"; // Default to member since profile.role doesn't exist
    
    const permissionMatrix: Record<string, TeamPermissions> = {
      admin: {
        can_view_jobs: true,
        can_view_applications: true,
        can_manage_applications: true,
        can_view_analytics: true,
        can_manage_team: true,
        can_manage_billing: true,
        can_manage_settings: true,
      },
      member: {
        can_view_jobs: true,
        can_view_applications: true,
        can_manage_applications: true,
        can_view_analytics: true,
        can_manage_team: false,
        can_manage_billing: false,
        can_manage_settings: false,
      },
      viewer: {
        can_view_jobs: true,
        can_view_applications: true,
        can_manage_applications: false,
        can_view_analytics: false,
        can_manage_team: false,
        can_manage_billing: false,
        can_manage_settings: false,
      },
    };

    return permissionMatrix[role]?.[action] || false;
  }, []);

  // Get team statistics
  const getTeamStats = useCallback(() => {
    if (!teamAnalytics) return null;

    return {
      totalMembers: teamAnalytics.total_members,
      activeMembers: teamAnalytics.active_members,
      totalApplications: teamAnalytics.total_applications,
      successRate: teamAnalytics.success_rate,
      averageResponseTime: teamAnalytics.average_response_time,
      topPerformer: teamAnalytics.top_performer,
      utilizationRate: teamAnalytics.active_members / teamAnalytics.total_members * 100,
    };
  }, [teamAnalytics]);

  // Open/close invitation modal
  const openInvitationModal = useCallback(() => {
    setTeamState(prev => ({ ...prev, invitationModalOpen: true }));
  }, []);

  const closeInvitationModal = useCallback(() => {
    setTeamState(prev => ({ ...prev, invitationModalOpen: false }));
  }, []);

  // Select member for details
  const selectMember = useCallback((member: TeamMember | null) => {
    setTeamState(prev => ({ ...prev, selectedMember: member }));
  }, []);

  return {
    // Data
    teamMembers,
    invitations,
    teamSettings,
    teamAnalytics,
    
    // Loading states
    isLoading: {
      members: membersLoading,
      invitations: invitationsLoading,
      settings: settingsLoading,
      analytics: analyticsLoading,
      inviting: inviteMemberMutation.isPending,
      updatingRole: updateRoleMutation.isPending,
    },
    
    // Errors
    errors: {
      members: membersError,
    },
    
    // Actions
    inviteMember,
    updateMemberRole,
    removeTeamMember,
    revokeInvitation,
    updateTeamSettings,
    
    // Utilities
    getMemberById,
    getActiveMembers,
    getMembersByRole,
    canPerformAction,
    getTeamStats,
    
    // UI State
    teamState,
    openInvitationModal,
    closeInvitationModal,
    selectMember,
    
    // Refetch functions
    refetchMembers,
    refetchInvitations,
    refetchSettings,
  };
}
