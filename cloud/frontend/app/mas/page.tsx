"use client";

import { useEffect, useState } from "react";
import { Activity, Brain, CheckCircle, AlertTriangle, Clock, TrendingUp } from "lucide-react";

interface AgentHealth {
    state: string;
    healthy: boolean;
    success_rate: number;
    tasks_completed: number;
    tasks_failed: number;
}

interface SystemHealth {
    system_healthy: boolean;
    agents: Record<string, AgentHealth>;
    timestamp: string;
}

interface Task {
    task_id: string;
    task_type: string;
    priority: number;
    status: string;
    created_at: string;
    parameters?: any;
}

interface Decision {
    type: string;
    timestamp: string;
    reason: string;
    should_irrigate?: boolean;
    should_fertilize?: boolean;
    duration_minutes?: number;
    soil_moisture?: number;
}

interface FieldStatus {
    farm_id: string;
    crop_health_score: number;
    crop_growth_stage: string;
    anomaly_detected: boolean;
    conditions: {
        temperature: number;
        humidity: number;
        light: number;
        soil_moisture: number;
    };
}

export default function MultiAgentSystemPage() {
    const [health, setHealth] = useState<SystemHealth | null>(null);
    const [activeTasks, setActiveTasks] = useState<Task[]>([]);
    const [decisions, setDecisions] = useState<Decision[]>([]);
    const [fieldStatus, setFieldStatus] = useState<FieldStatus | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 5000); // Refresh every 5 seconds
        return () => clearInterval(interval);
    }, []);

    const fetchData = async () => {
        try {
            // Fetch health
            const healthRes = await fetch("http://localhost:8000/mas/health");
            if (healthRes.ok) {
                const healthData = await healthRes.json();
                setHealth(healthData);
            }

            // Fetch active tasks
            const tasksRes = await fetch("http://localhost:8000/mas/tasks/active");
            if (tasksRes.ok) {
                const tasksData = await tasksRes.json();
                setActiveTasks(tasksData.tasks || []);
            }

            // Fetch recent decisions
            const decisionsRes = await fetch("http://localhost:8000/mas/decisions?days=1");
            if (decisionsRes.ok) {
                const decisionsData = await decisionsRes.json();
                setDecisions(decisionsData.decisions?.slice(0, 5) || []);
            }

            // Fetch field status
            const fieldRes = await fetch("http://localhost:8000/mas/field-status");
            if (fieldRes.ok) {
                const fieldData = await fieldRes.json();
                setFieldStatus(fieldData);
            }

            setLoading(false);
        } catch (error) {
            console.error("Error fetching MAS data:", error);
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 p-8 flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-green-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading Multi-Agent System...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-4xl font-bold text-gray-800 mb-2 flex items-center gap-3">
                        <Brain className="w-10 h-10 text-green-600" />
                        Multi-Agent System
                    </h1>
                    <p className="text-gray-600">Autonomous farm operations with intelligent agents</p>
                </div>

                {/* System Health Status */}
                <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                            <Activity className="w-6 h-6 text-blue-600" />
                            System Health
                        </h2>
                        <div className={`px-4 py-2 rounded-full ${health?.system_healthy ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                            {health?.system_healthy ? '✓ Healthy' : '✗ Issues Detected'}
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        {health && Object.entries(health.agents).map(([agentId, agentData]) => (
                            <div key={agentId} className="border border-gray-200 rounded-lg p-4">
                                <div className="flex items-center justify-between mb-2">
                                    <h3 className="font-semibold text-gray-700 text-sm">
                                        {agentId.replace('_', ' ').replace(/\d+/, '').trim()}
                                    </h3>
                                    {agentData.healthy ? (
                                        <CheckCircle className="w-5 h-5 text-green-500" />
                                    ) : (
                                        <AlertTriangle className="w-5 h-5 text-red-500" />
                                    )}
                                </div>
                                <div className="space-y-1 text-sm">
                                    <p className="text-gray-600">State: <span className="font-medium text-gray-800">{agentData.state}</span></p>
                                    <p className="text-gray-600">Success: <span className="font-medium text-gray-800">{(agentData.success_rate * 100).toFixed(1)}%</span></p>
                                    <p className="text-gray-600">Tasks: <span className="font-medium text-gray-800">{agentData.tasks_completed}</span></p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Field Status */}
                {fieldStatus && (
                    <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
                        <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                            <TrendingUp className="w-6 h-6 text-green-600" />
                            Field Status
                        </h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            <div className="border border-gray-200 rounded-lg p-4">
                                <p className="text-gray-600 text-sm mb-1">Crop Health Score</p>
                                <p className="text-3xl font-bold text-green-600">{fieldStatus.crop_health_score.toFixed(1)}%</p>
                            </div>
                            <div className="border border-gray-200 rounded-lg p-4">
                                <p className="text-gray-600 text-sm mb-1">Growth Stage</p>
                                <p className="text-xl font-semibold text-gray-800 capitalize">{fieldStatus.crop_growth_stage}</p>
                            </div>
                            <div className="border border-gray-200 rounded-lg p-4">
                                <p className="text-gray-600 text-sm mb-1">Anomaly Status</p>
                                <p className={`text-xl font-semibold ${fieldStatus.anomaly_detected ? 'text-red-600' : 'text-green-600'}`}>
                                    {fieldStatus.anomaly_detected ? '⚠️ Detected' : '✓ Normal'}
                                </p>
                            </div>
                        </div>

                        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div className="text-center p-3 bg-gray-50 rounded-lg">
                                <p className="text-gray-600 text-sm">Temperature</p>
                                <p className="text-xl font-bold text-gray-800">{fieldStatus.conditions.temperature}°C</p>
                            </div>
                            <div className="text-center p-3 bg-gray-50 rounded-lg">
                                <p className="text-gray-600 text-sm">Humidity</p>
                                <p className="text-xl font-bold text-gray-800">{fieldStatus.conditions.humidity}%</p>
                            </div>
                            <div className="text-center p-3 bg-gray-50 rounded-lg">
                                <p className="text-gray-600 text-sm">Light</p>
                                <p className="text-xl font-bold text-gray-800">{fieldStatus.conditions.light} lux</p>
                            </div>
                            <div className="text-center p-3 bg-gray-50 rounded-lg">
                                <p className="text-gray-600 text-sm">Soil Moisture</p>
                                <p className="text-xl font-bold text-gray-800">{fieldStatus.conditions.soil_moisture}%</p>
                            </div>
                        </div>
                    </div>
                )}

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Active Tasks */}
                    <div className="bg-white rounded-lg shadow-lg p-6">
                        <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                            <Clock className="w-6 h-6 text-orange-600" />
                            Active Tasks ({activeTasks.length})
                        </h2>
                        <div className="space-y-3">
                            {activeTasks.length === 0 ? (
                                <p className="text-gray-500 text-center py-8">No active tasks</p>
                            ) : (
                                activeTasks.map((task) => (
                                    <div key={task.task_id} className="border border-gray-200 rounded-lg p-4">
                                        <div className="flex items-center justify-between mb-2">
                                            <h3 className="font-semibold text-gray-800 capitalize">{task.task_type}</h3>
                                            <span className={`px-2 py-1 rounded text-xs font-medium ${task.priority === 4 ? 'bg-red-100 text-red-800' :
                                                    task.priority === 3 ? 'bg-orange-100 text-orange-800' :
                                                        task.priority === 2 ? 'bg-yellow-100 text-yellow-800' :
                                                            'bg-gray-100 text-gray-800'
                                                }`}>
                                                Priority: {task.priority}
                                            </span>
                                        </div>
                                        <p className="text-sm text-gray-600">Status: <span className="font-medium">{task.status}</span></p>
                                        <p className="text-xs text-gray-500 mt-1">
                                            Created: {new Date(task.created_at).toLocaleString()}
                                        </p>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>

                    {/* Recent Decisions */}
                    <div className="bg-white rounded-lg shadow-lg p-6">
                        <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                            <Brain className="w-6 h-6 text-purple-600" />
                            Recent Decisions ({decisions.length})
                        </h2>
                        <div className="space-y-3">
                            {decisions.length === 0 ? (
                                <p className="text-gray-500 text-center py-8">No decisions yet</p>
                            ) : (
                                decisions.map((decision, idx) => (
                                    <div key={idx} className="border border-gray-200 rounded-lg p-4">
                                        <div className="flex items-center justify-between mb-2">
                                            <h3 className="font-semibold text-gray-800 capitalize">{decision.type}</h3>
                                            <span className={`px-2 py-1 rounded text-xs font-medium ${decision.should_irrigate || decision.should_fertilize
                                                    ? 'bg-green-100 text-green-800'
                                                    : 'bg-gray-100 text-gray-800'
                                                }`}>
                                                {decision.should_irrigate || decision.should_fertilize ? 'Action Taken' : 'No Action'}
                                            </span>
                                        </div>
                                        <p className="text-sm text-gray-600">{decision.reason}</p>
                                        {decision.duration_minutes && (
                                            <p className="text-xs text-gray-500 mt-1">Duration: {decision.duration_minutes} minutes</p>
                                        )}
                                        <p className="text-xs text-gray-500 mt-1">
                                            {new Date(decision.timestamp).toLocaleString()}
                                        </p>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>

                {/* Quick Actions */}
                <div className="mt-6 bg-white rounded-lg shadow-lg p-6">
                    <h2 className="text-2xl font-bold text-gray-800 mb-4">Quick Actions</h2>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <a
                            href="http://localhost:8000/docs#/Multi-Agent%20System"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="bg-blue-500 hover:bg-blue-600 text-white rounded-lg p-4 text-center transition-colors"
                        >
                            <p className="font-semibold">API Docs</p>
                            <p className="text-sm opacity-90">View endpoints</p>
                        </a>
                        <a
                            href="http://localhost:8000/mas/metrics"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="bg-green-500 hover:bg-green-600 text-white rounded-lg p-4 text-center transition-colors"
                        >
                            <p className="font-semibold">Metrics</p>
                            <p className="text-sm opacity-90">System performance</p>
                        </a>
                        <a
                            href="http://localhost:8000/mas/decisions"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="bg-purple-500 hover:bg-purple-600 text-white rounded-lg p-4 text-center transition-colors"
                        >
                            <p className="font-semibold">All Decisions</p>
                            <p className="text-sm opacity-90">View history</p>
                        </a>
                        <a
                            href="/"
                            className="bg-gray-500 hover:bg-gray-600 text-white rounded-lg p-4 text-center transition-colors"
                        >
                            <p className="font-semibold">Main Dashboard</p>
                            <p className="text-sm opacity-90">Back to home</p>
                        </a>
                    </div>
                </div>
            </div>
        </div>
    );
}
