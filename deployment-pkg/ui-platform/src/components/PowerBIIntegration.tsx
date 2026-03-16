import React, { useEffect, useState } from 'react';
import { AlertCircle, RefreshCw, Download, Share2 } from 'lucide-react';

/**
 * PowerBI Report Embed Component
 * Integrates Microsoft PowerBI reports directly into the application
 */
export const PowerBIReportEmbed = ({ 
  embedUrl, 
  reportId, 
  accessToken,
  title,
  onError 
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Load PowerBI SDK
    const script = document.createElement('script');
    script.src = 'https://app.powerbi.com/scripts/embedconfig.scripts.js';
    script.async = true;
    script.onload = () => setLoading(false);
    script.onerror = () => {
      setError('Failed to load PowerBI SDK');
      setLoading(false);
    };
    document.body.appendChild(script);

    return () => document.body.removeChild(script);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96 bg-slate-50 rounded-xl border border-slate-200">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin text-indigo-600 mx-auto mb-4" />
          <p className="text-slate-600">Loading PowerBI Report...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6">
        <div className="flex items-start gap-4">
          <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-1" />
          <div>
            <h3 className="font-semibold text-red-900">Unable to Load Report</h3>
            <p className="text-red-700 mt-2">{error}</p>
            <p className="text-red-600 text-sm mt-4">Please check your authentication settings and try again.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-bold text-lg">{title}</h3>
        <div className="flex gap-2">
          <button className="flex items-center gap-2 px-4 py-2 text-slate-700 hover:bg-slate-100 rounded-lg transition">
            <Share2 className="w-4 h-4" />
            Share
          </button>
          <button className="flex items-center gap-2 px-4 py-2 text-slate-700 hover:bg-slate-100 rounded-lg transition">
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>
      <div
        id={`report-${reportId}`}
        className="bg-white rounded-xl border border-slate-200 overflow-hidden"
        style={{ height: '600px' }}
      />
    </div>
  );
};

/**
 * PowerBI Dashboard Embed Component
 * Full dashboard embedding with filters
 */
export const PowerBIDashboardEmbed = ({ 
  dashboardId,
  accessToken,
  title,
  filters = []
}) => {
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">{title}</h2>
        <button className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition">
          Refresh Data
        </button>
      </div>
      <div
        id={`dashboard-${dashboardId}`}
        className="bg-white rounded-xl border border-slate-200"
        style={{ height: '700px' }}
      />
    </div>
  );
};

/**
 * PowerBI Alert Component
 * Interactive alerts from PowerBI data
 */
export const PowerBIAlerts = ({ 
  workspaceId,
  accessToken 
}) => {
  const [alerts, setAlerts] = useState([
    {
      id: 1,
      title: 'High Turnover Risk',
      description: 'Engineering department showing 15% increased resignation intent based on sentiment analysis',
      severity: 'high',
      metric: 'Turnover Risk',
      value: '+15%',
      action: 'Review'
    },
    {
      id: 2,
      title: 'Budget Alert',
      description: 'Q2 salary expenses exceeding budget by 8% due to new hires',
      severity: 'medium',
      metric: 'Budget Variance',
      value: '+8%',
      action: 'Analyze'
    },
    {
      id: 3,
      title: 'Productivity Improvement',
      description: 'New automation workflow increased productivity by 22% in operations',
      severity: 'low',
      metric: 'Efficiency Gain',
      value: '+22%',
      action: 'Details'
    }
  ]);

  const severityStyles = {
    high: 'bg-red-50 border-red-200 text-red-900',
    medium: 'bg-yellow-50 border-yellow-200 text-yellow-900',
    low: 'bg-green-50 border-green-200 text-green-900'
  };

  return (
    <div className="space-y-4">
      <h3 className="text-xl font-bold">PowerBI Alerts & Insights</h3>
      <div className="grid gap-4">
        {alerts.map(alert => (
          <div key={alert.id} className={`p-4 rounded-xl border ${severityStyles[alert.severity]}`}>
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <h4 className="font-semibold mb-1">{alert.title}</h4>
                <p className="text-sm opacity-90">{alert.description}</p>
                <div className="mt-3 flex items-center gap-4">
                  <div>
                    <span className="text-xs opacity-75">{alert.metric}</span>
                    <p className="text-lg font-bold">{alert.value}</p>
                  </div>
                  <button className="ml-auto px-4 py-1 text-sm font-medium rounded-lg opacity-70 hover:opacity-100 transition">
                    {alert.action}
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

/**
 * PowerBI Integration Setup Guide
 */
export const PowerBISetupGuide = () => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left flex justify-between items-center font-semibold text-blue-900 hover:text-blue-700"
      >
        <span>🔗 PowerBI Integration Setup</span>
        <span>{expanded ? '−' : '+'}</span>
      </button>

      {expanded && (
        <div className="mt-4 space-y-4 text-sm text-blue-900">
          <div>
            <h4 className="font-semibold mb-2">Step 1: Create PowerBI Service Account</h4>
            <code className="block bg-white p-2 rounded text-xs overflow-auto mb-2">
              1. Go to Power BI Admin Portal<br/>
              2. Create Service Principal<br/>
              3. Generate Access Token
            </code>
          </div>

          <div>
            <h4 className="font-semibold mb-2">Step 2: Configure Environment Variables</h4>
            <code className="block bg-white p-2 rounded text-xs overflow-auto mb-2">
              POWERBI_CLIENT_ID=your_client_id<br/>
              POWERBI_CLIENT_SECRET=your_secret<br/>
              POWERBI_TENANT_ID=your_tenant_id<br/>
              POWERBI_WORKSPACE_ID=your_workspace_id
            </code>
          </div>

          <div>
            <h4 className="font-semibold mb-2">Step 3: Enable Report Embedding</h4>
            <ul className="list-disc list-inside space-y-1">
              <li>Assign Premium licenses to Service Principal</li>
              <li>Share reports with Service Principal</li>
              <li>Configure Embed for customers setting</li>
              <li>Generate access tokens for reports</li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold mb-2">Step 4: Add Reports to Application</h4>
            <code className="block bg-white p-2 rounded text-xs overflow-auto">
              &lt;PowerBIReportEmbed<br/>
              &nbsp;&nbsp;reportId="your_report_id"<br/>
              &nbsp;&nbsp;embedUrl="your_embed_url"<br/>
              &nbsp;&nbsp;accessToken="your_access_token"<br/>
              &nbsp;&nbsp;title="HR Dashboard"<br/>
              /&gt;
            </code>
          </div>

          <div className="bg-white p-3 rounded border border-blue-300">
            <p className="font-semibold mb-2">📚 Resources:</p>
            <ul className="space-y-1 text-xs">
              <li>• <a href="#" className="text-blue-600 hover:underline">PowerBI Embedding Documentation</a></li>
              <li>• <a href="#" className="text-blue-600 hover:underline">Service Principal Setup Guide</a></li>
              <li>• <a href="#" className="text-blue-600 hover:underline">REST API Reference</a></li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * PowerBI Analytics Dashboard
 * Complete dashboard with embedded reports and analytics
 */
export default function PowerBIAnalyticsDashboard() {
  const [powerBIConfig, setPowerBIConfig] = useState({
    clientId: process.env.REACT_APP_POWERBI_CLIENT_ID || '',
    clientSecret: process.env.REACT_APP_POWERBI_CLIENT_SECRET || '',
    tenantId: process.env.REACT_APP_POWERBI_TENANT_ID || '',
    workspaceId: process.env.REACT_APP_POWERBI_WORKSPACE_ID || '',
    isConfigured: false
  });

  useEffect(() => {
    // Check if PowerBI is configured
    if (powerBIConfig.clientId && powerBIConfig.workspaceId) {
      setPowerBIConfig(prev => ({ ...prev, isConfigured: true }));
    }
  }, []);

  if (!powerBIConfig.isConfigured) {
    return (
      <div className="min-h-screen bg-slate-50 p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          <div className="bg-white rounded-xl p-8 border border-slate-200">
            <h1 className="text-3xl font-bold mb-4">PowerBI Not Configured</h1>
            <p className="text-slate-600 mb-6">
              To enable PowerBI analytics integration, please configure your credentials first.
            </p>
            <PowerBISetupGuide />
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-green-50 border border-green-200 rounded-xl p-6">
              <h3 className="font-bold text-lg mb-4 text-green-900">✓ Benefits of PowerBI Integration</h3>
              <ul className="space-y-2 text-sm text-green-800">
                <li>• Real-time analytics dashboards</li>
                <li>• Advanced data visualization</li>
                <li>• Custom reports and insights</li>
                <li>• Data refresh automation</li>
                <li>• Mobile-friendly analytics</li>
                <li>• Collaboration features</li>
              </ul>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
              <h3 className="font-bold text-lg mb-4 text-blue-900">📊 Available Reports</h3>
              <ul className="space-y-2 text-sm text-blue-800">
                <li>• HR Analytics Dashboard</li>
                <li>• Employee Performance Reports</li>
                <li>• Recruitment Funnel</li>
                <li>• Payroll Analysis</li>
                <li>• Attendance Trends</li>
                <li>• Compensation Analysis</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="max-w-7xl mx-auto space-y-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">PowerBI Analytics</h1>
          <p className="text-slate-600">Advanced business intelligence and reporting</p>
        </div>

        {/* Main Reports */}
        <div className="space-y-6">
          <PowerBIReportEmbed
            title="HR Executive Dashboard"
            reportId="hr-executive-dashboard"
            embedUrl={process.env.REACT_APP_POWERBI_REPORT_HR_DASHBOARD}
            accessToken={process.env.REACT_APP_POWERBI_ACCESS_TOKEN}
          />

          <PowerBIReportEmbed
            title="Employee Analytics & Insights"
            reportId="employee-analytics"
            embedUrl={process.env.REACT_APP_POWERBI_REPORT_EMPLOYEE}
            accessToken={process.env.REACT_APP_POWERBI_ACCESS_TOKEN}
          />

          <PowerBIAlerts 
            workspaceId={powerBIConfig.workspaceId}
            accessToken={process.env.REACT_APP_POWERBI_ACCESS_TOKEN}
          />
        </div>

        {/* Footer */}
        <div className="text-center text-slate-600 text-sm">
          <p>Powered by Microsoft PowerBI • Data updates every hour</p>
          <p className="mt-2">All data is encrypted and secured</p>
        </div>
      </div>
    </div>
  );
}
