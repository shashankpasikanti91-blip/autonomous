/**
 * RBAC Management Console Page
 * Users, roles, permissions, API keys, audit logs
 */

import React, { useState, useEffect } from "react";
import { MainLayout } from "../components/layouts/MainLayout";
import {
  Card,
  Button,
  Loading,
  ErrorAlert,
  Table,
  EmptyState,
  Modal,
  Stat,
} from "../components/common/UIComponents";
import { usePermission } from "../hooks";
import { userService } from "../services";
import { formatDate, formatDateTime } from "../utils";
import { USER_ROLES } from "../utils/constants";
import type { User, APIKey, AuditLogEntry } from "../types";

interface Tab {
  id: string;
  label: string;
  icon: string;
}

export const RBACManagement: React.FC = () => {
  const { can } = usePermission();

  const [activeTab, setActiveTab] = useState<"users" | "apikeys" | "audit">("users");
  const [users, setUsers] = useState<User[]>([]);
  const [apiKeys, setAPIKeys] = useState<APIKey[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showUserModal, setShowUserModal] = useState(false);
  const [showKeyModal, setShowKeyModal] = useState(false);
  const [actionInProgress, setActionInProgress] = useState(false);

  // Load data based on active tab
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);

      try {
        if (activeTab === "users") {
          const result = await userService.listUsers(undefined, 50);
          setUsers(result.items);
        } else if (activeTab === "apikeys") {
          const result = await userService.listAPIKeys(undefined, 50);
          setAPIKeys(result.items);
        } else if (activeTab === "audit") {
          const result = await userService.getAuditLogs(undefined, 100);
          setAuditLogs(result.items);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [activeTab]);

  const handleAssignRole = async (userId: string, newRole: string) => {
    if (confirm(`Change role to ${newRole}?`)) {
      setActionInProgress(true);
      try {
        const updated = await userService.assignRole(userId, newRole as any);
        setUsers(users.map((u) => (u.user_id === userId ? updated : u)));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to assign role");
      } finally {
        setActionInProgress(false);
      }
    }
  };

  const handleDisableUser = async (userId: string) => {
    if (confirm("Disable this user?")) {
      setActionInProgress(true);
      try {
        const updated = await userService.disableUser(userId);
        setUsers(users.map((u) => (u.user_id === userId ? updated : u)));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to disable user");
      } finally {
        setActionInProgress(false);
      }
    }
  };

  const handleRevokeKey = async (keyId: string) => {
    if (confirm("Revoke this API key?")) {
      setActionInProgress(true);
      try {
        const updated = await userService.revokeAPIKey(keyId);
        setAPIKeys(apiKeys.map((k) => (k.key_id === keyId ? updated : k)));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to revoke key");
      } finally {
        setActionInProgress(false);
      }
    }
  };

  const tabs: Tab[] = [
    { id: "users", label: "Users", icon: "👤" },
    { id: "apikeys", label: "API Keys", icon: "🔑" },
    { id: "audit", label: "Audit Logs", icon: "📋" },
  ];

  if (loading && activeTab === "users") return <Loading text="Loading users..." />;

  return (
    <MainLayout
      title="RBAC Management"
      breadcrumbs={[
        { label: "Dashboard", href: "/dashboard" },
        { label: "RBAC Management" },
      ]}
    >
      <div className="space-y-6">
        {error && <ErrorAlert message={error} />}

        {/* Tab Navigation */}
        <div className="flex space-x-2 bg-gray-800 rounded-lg p-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center space-x-2 px-4 py-2 rounded transition-colors ${
                activeTab === tab.id
                  ? "bg-blue-600 text-white"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Users Tab */}
        {activeTab === "users" && (
          <>
            <div className="flex items-center justify-between">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 flex-1">
                <Stat label="Total Users" value={users.length} icon="👥" />
                <Stat
                  label="Active Users"
                  value={users.filter((u) => !u.disabled).length}
                  icon="✅"
                />
                <Stat
                  label="Disabled"
                  value={users.filter((u) => u.disabled).length}
                  icon="🔒"
                />
              </div>
              {can("rbac:write") && (
                <Button onClick={() => setShowUserModal(true)}>
                  ➕ Add User
                </Button>
              )}
            </div>

            {loading ? (
              <Loading text="Loading users..." />
            ) : users.length === 0 ? (
              <EmptyState
                icon="👤"
                title="No Users"
                description="Add your first user to get started"
                action={
                  can("rbac:write") && (
                    <Button onClick={() => setShowUserModal(true)}>
                      Add User
                    </Button>
                  )
                }
              />
            ) : (
              <Card>
                <Table
                  columns={[
                    {
                      key: "email",
                      label: "Email",
                      render: (value, row: any) => (
                        <div>
                          <p className="font-semibold">{value}</p>
                          <p className="text-xs text-gray-400">{row.name}</p>
                        </div>
                      ),
                    },
                    {
                      key: "role",
                      label: "Role",
                      render: (value) => (
                        <span className="bg-blue-900 text-blue-200 px-2 py-1 rounded text-xs font-semibold">
                          {String(value).toUpperCase()}
                        </span>
                      ),
                    },
                    {
                      key: "disabled",
                      label: "Status",
                      render: (value) => (
                        <span
                          className={`px-2 py-1 rounded text-xs font-semibold ${
                            value
                              ? "bg-red-900 text-red-200"
                              : "bg-green-900 text-green-200"
                          }`}
                        >
                          {value ? "DISABLED" : "ACTIVE"}
                        </span>
                      ),
                    },
                    {
                      key: "last_login",
                      label: "Last Login",
                      render: (value) =>
                        value ? formatDateTime(value as string) : "Never",
                    },
                    {
                      key: "mfa_enabled",
                      label: "MFA",
                      render: (value) => (
                        <span>{value ? "✅ Enabled" : "⚠️ Disabled"}</span>
                      ),
                    },
                    {
                      key: "user_id",
                      label: "Actions",
                      align: "right",
                      render: (value, row: any) => (
                        <div className="flex gap-2 justify-end">
                          {can("rbac:write") && (
                            <>
                              <select
                                value={row.role}
                                onChange={(e) =>
                                  handleAssignRole(value as string, e.target.value)
                                }
                                disabled={actionInProgress}
                                className="px-2 py-1 bg-gray-700 rounded text-xs"
                              >
                                {Object.entries(USER_ROLES).map(([key]) => (
                                  <option key={key} value={key}>
                                    {key.toUpperCase()}
                                  </option>
                                ))}
                              </select>
                              {!row.disabled && (
                                <Button
                                  variant="danger"
                                  size="sm"
                                  onClick={() => handleDisableUser(value as string)}
                                  disabled={actionInProgress}
                                >
                                  Disable
                                </Button>
                              )}
                            </>
                          )}
                        </div>
                      ),
                    },
                  ]}
                  data={users}
                />
              </Card>
            )}
          </>
        )}

        {/* API Keys Tab */}
        {activeTab === "apikeys" && (
          <>
            <div className="flex items-center justify-between">
              <Stat label="Total API Keys" value={apiKeys.length} icon="🔑" />
              {can("rbac:write") && (
                <Button onClick={() => setShowKeyModal(true)}>
                  ➕ Create Key
                </Button>
              )}
            </div>

            {loading ? (
              <Loading text="Loading API keys..." />
            ) : apiKeys.length === 0 ? (
              <EmptyState
                icon="🔑"
                title="No API Keys"
                description="Create your first API key to get started"
                action={
                  can("rbac:write") && (
                    <Button onClick={() => setShowKeyModal(true)}>
                      Create API Key
                    </Button>
                  )
                }
              />
            ) : (
              <Card>
                <Table
                  columns={[
                    {
                      key: "name",
                      label: "Name",
                      render: (value) => (
                        <span className="font-semibold">{value}</span>
                      ),
                    },
                    {
                      key: "key_prefix",
                      label: "Key Prefix",
                      render: (value) => (
                        <span className="font-mono text-xs">{value}...</span>
                      ),
                    },
                    {
                      key: "created_at",
                      label: "Created",
                      render: (value) => formatDate(value as string),
                    },
                    {
                      key: "last_used",
                      label: "Last Used",
                      render: (value) =>
                        value ? formatDateTime(value as string) : "Never",
                    },
                    {
                      key: "revoked",
                      label: "Status",
                      render: (value) => (
                        <span
                          className={`px-2 py-1 rounded text-xs font-semibold ${
                            value
                              ? "bg-red-900 text-red-200"
                              : "bg-green-900 text-green-200"
                          }`}
                        >
                          {value ? "REVOKED" : "ACTIVE"}
                        </span>
                      ),
                    },
                    {
                      key: "key_id",
                      label: "Actions",
                      align: "right",
                      render: (value, row: any) => (
                        <div>
                          {!row.revoked && can("rbac:write") && (
                            <Button
                              variant="danger"
                              size="sm"
                              onClick={() => handleRevokeKey(value as string)}
                              disabled={actionInProgress}
                            >
                              Revoke
                            </Button>
                          )}
                        </div>
                      ),
                    },
                  ]}
                  data={apiKeys}
                />
              </Card>
            )}
          </>
        )}

        {/* Audit Logs Tab */}
        {activeTab === "audit" && (
          <>
            <Stat
              label="Total Audit Events"
              value={auditLogs.length}
              icon="📋"
            />

            {loading ? (
              <Loading text="Loading audit logs..." />
            ) : auditLogs.length === 0 ? (
              <EmptyState
                icon="📋"
                title="No Audit Logs"
                description="Actions will be logged here"
              />
            ) : (
              <Card>
                <Table
                  columns={[
                    {
                      key: "action",
                      label: "Action",
                      render: (value) => (
                        <span className="font-medium capitalize">
                          {String(value).replace(/_/g, " ")}
                        </span>
                      ),
                    },
                    {
                      key: "resource_type",
                      label: "Resource",
                      render: (value) => (
                        <span className="text-sm capitalize">
                          {String(value).replace(/_/g, " ")}
                        </span>
                      ),
                    },
                    {
                      key: "status",
                      label: "Status",
                      render: (value) => (
                        <span
                          className={`px-2 py-1 rounded text-xs font-semibold ${
                            value === "success"
                              ? "bg-green-900 text-green-200"
                              : "bg-red-900 text-red-200"
                          }`}
                        >
                          {String(value).toUpperCase()}
                        </span>
                      ),
                    },
                    {
                      key: "timestamp",
                      label: "Time",
                      render: (value) => formatDateTime(value as string, "short"),
                    },
                    {
                      key: "ip_address",
                      label: "IP Address",
                      render: (value) => (
                        <span className="font-mono text-xs">{value || "N/A"}</span>
                      ),
                    },
                  ]}
                  data={auditLogs}
                />
              </Card>
            )}
          </>
        )}

        {/* User Modal */}
        <Modal
          isOpen={showUserModal}
          title="Add New User"
          onClose={() => setShowUserModal(false)}
        >
          <div className="space-y-4">
            <input
              type="email"
              placeholder="Email"
              className="w-full px-3 py-2 bg-gray-700 rounded border border-gray-600 text-white"
            />
            <select className="w-full px-3 py-2 bg-gray-700 rounded border border-gray-600 text-white">
              {Object.entries(USER_ROLES).map(([key, role]) => (
                <option key={key} value={key}>
                  {role.name}
                </option>
              ))}
            </select>
            <div className="flex gap-2">
              <Button
                variant="primary"
                onClick={() => setShowUserModal(false)}
              >
                Add User
              </Button>
              <Button
                variant="secondary"
                onClick={() => setShowUserModal(false)}
              >
                Cancel
              </Button>
            </div>
          </div>
        </Modal>

        {/* API Key Modal */}
        <Modal
          isOpen={showKeyModal}
          title="Create API Key"
          onClose={() => setShowKeyModal(false)}
        >
          <div className="space-y-4">
            <input
              type="text"
              placeholder="Key Name"
              className="w-full px-3 py-2 bg-gray-700 rounded border border-gray-600 text-white"
            />
            <div className="bg-gray-700 p-3 rounded">
              <p className="text-xs text-gray-400">Key Scopes (select multiple)</p>
              {["read", "write", "delete"].map((scope) => (
                <label key={scope} className="flex items-center mt-2">
                  <input
                    type="checkbox"
                    defaultChecked
                    className="rounded"
                  />
                  <span className="ml-2 text-sm">{scope.toUpperCase()}</span>
                </label>
              ))}
            </div>
            <div className="flex gap-2">
              <Button
                variant="primary"
                onClick={() => setShowKeyModal(false)}
              >
                Create Key
              </Button>
              <Button
                variant="secondary"
                onClick={() => setShowKeyModal(false)}
              >
                Cancel
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    </MainLayout>
  );
};
