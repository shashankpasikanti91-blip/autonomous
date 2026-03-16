import React, { useState } from 'react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Cell, ScatterChart, Scatter, RadarChart, PolarGrid, PolarAngleAxis,
  PolarRadiusAxis, Radar
} from 'recharts';
import {
  TrendingUp, TrendingDown, Users, Target, Activity, AlertCircle,
  Download, Filter, Calendar, Settings
} from 'lucide-react';

// Mock Data
const employeeData = [
  { month: 'Jan', employees: 450, newHires: 12, turnover: 5 },
  { month: 'Feb', employees: 465, newHires: 15, turnover: 3 },
  { month: 'Mar', employees: 480, newHires: 18, turnover: 4 },
  { month: 'Apr', employees: 510, newHires: 30, turnover: 2 },
  { month: 'May', employees: 545, newHires: 35, turnover: 6 },
  { month: 'Jun', employees: 580, newHires: 40, turnover: 8 }
];

const departmentData = [
  { name: 'Engineering', value: 235, fill: '#6366f1' },
  { name: 'Sales', value: 180, fill: '#ec4899' },
  { name: 'Marketing', value: 120, fill: '#0ea5e9' },
  { name: 'Operations', value: 95, fill: '#10b981' },
  { name: 'HR', value: 45, fill: '#f97316' }
];

const performanceData = [
  { month: 'Week 1', performance: 78 },
  { month: 'Week 2', performance: 82 },
  { month: 'Week 3', performance: 85 },
  { month: 'Week 4', performance: 88 },
  { month: 'Week 5', performance: 92 },
  { month: 'Week 6', performance: 95 }
];

const salaryData = [
  { designation: 'Manager', avgSalary: 120000 },
  { designation: 'Senior Dev', avgSalary: 95000 },
  { designation: 'Developer', avgSalary: 75000 },
  { designation: 'Junior Dev', avgSalary: 55000 },
  { designation: 'Intern', avgSalary: 30000 }
];

const attendanceData = [
  { name: 'Present', value: 520, fill: '#10b981' },
  { name: 'Absent', value: 25, fill: '#ef4444' },
  { name: 'Leave', value: 35, fill: '#f97316' }
];

const competencyData = [
  { subject: 'Technical', A: 85, B: 90, fullMark: 100 },
  { subject: 'Communication', A: 78, B: 88, fullMark: 100 },
  { subject: 'Leadership', A: 80, B: 85, fullMark: 100 },
  { subject: 'Teamwork', A: 88, B: 92, fullMark: 100 },
  { subject: 'Problem Solving', A: 82, B: 86, fullMark: 100 }
];

const KPICard = ({ title, value, change, icon: Icon, trend }) => (
  <div className="bg-white rounded-xl p-6 border border-slate-200 hover:shadow-lg transition">
    <div className="flex justify-between items-start mb-4">
      <div>
        <p className="text-slate-600 text-sm font-medium">{title}</p>
        <h3 className="text-2xl font-bold mt-2">{value}</h3>
      </div>
      <div className={`p-3 rounded-lg ${trend === 'up' ? 'bg-green-100' : 'bg-red-100'}`}>
        <Icon className={`w-6 h-6 ${trend === 'up' ? 'text-green-600' : 'text-red-600'}`} />
      </div>
    </div>
    <div className={`flex items-center gap-1 text-sm ${trend === 'up' ? 'text-green-600' : 'text-red-600'}`}>
      {trend === 'up' ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
      <span>{change} vs last month</span>
    </div>
  </div>
);

const ChartCard = ({ title, children, subtitle }) => (
  <div className="bg-white rounded-xl p-6 border border-slate-200 hover:shadow-lg transition">
    <div className="flex justify-between items-start mb-6">
      <div>
        <h3 className="font-bold text-lg">{title}</h3>
        {subtitle && <p className="text-slate-500 text-sm mt-1">{subtitle}</p>}
      </div>
      <button className="text-slate-400 hover:text-slate-600 transition">
        <Download className="w-5 h-5" />
      </button>
    </div>
    {children}
  </div>
);

export default function AdvancedAnalytics() {
  const [dateRange, setDateRange] = useState('6m');
  const [selectedDept, setSelectedDept] = useState('all');

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Analytics Dashboard</h1>
            <p className="text-slate-600 text-sm mt-1">Real-time HR metrics and insights</p>
          </div>
          <div className="flex gap-4">
            <div className="flex items-center gap-2 bg-slate-100 rounded-lg px-4 py-2">
              <Calendar className="w-5 h-5 text-slate-600" />
              <select className="bg-transparent border-none font-medium cursor-pointer">
                <option>Last 6 Months</option>
                <option>This Year</option>
                <option>Custom Range</option>
              </select>
            </div>
            <button className="flex items-center gap-2 bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 transition">
              <Filter className="w-5 h-5" />
              Export
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* KPIs */}
        <div className="grid md:grid-cols-5 gap-4 mb-8">
          <KPICard title="Total Employees" value="580" change="+12%" icon={Users} trend="up" />
          <KPICard title="New Hires (YTD)" value="145" change="+8%" icon={Activity} trend="up" />
          <KPICard title="Turnover Rate" value="2.1%" change="-0.3%" icon={TrendingDown} trend="down" />
          <KPICard title="Avg Performance" value="88.5%" change="+4.2%" icon={Target} trend="up" />
          <KPICard title="Utilization Rate" value="92%" change="+1.5%" icon={AlertCircle} trend="up" />
        </div>

        {/* Main Charts Grid */}
        <div className="grid lg:grid-cols-3 gap-6 mb-8">
          {/* Employee Growth */}
          <div className="lg:col-span-2">
            <ChartCard title="Employee Growth Trend" subtitle="Monthly employee count and hiring">
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={employeeData}>
                  <defs>
                    <linearGradient id="colorEmployees" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366f1" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Area type="monotone" dataKey="employees" stroke="#6366f1" fillOpacity={1} fill="url(#colorEmployees)" />
                </AreaChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>

          {/* Department Distribution */}
          <ChartCard title="Department Breakdown" subtitle="Headcount by department">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={departmentData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {departmentData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        {/* Second Row Charts */}
        <div className="grid lg:grid-cols-3 gap-6 mb-8">
          {/* Performance Trend */}
          <div className="lg:col-span-2">
            <ChartCard title="Performance Metrics" subtitle="Weekly average performance score">
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis domain={[0, 100]} />
                  <Tooltip formatter={(value) => `${value}%`} />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="performance"
                    stroke="#ec4899"
                    strokeWidth={3}
                    dot={{ fill: '#ec4899', r: 5 }}
                    activeDot={{ r: 7 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>

          {/* Attendance Overview */}
          <ChartCard title="Today's Attendance" subtitle="Current attendance status">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={attendanceData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {attendanceData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        {/* Bottom Row */}
        <div className="grid lg:grid-cols-2 gap-6 mb-8">
          {/* Salary Analysis */}
          <ChartCard title="Salary Analysis by Designation" subtitle="Average compensation by role">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={salaryData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="designation" />
                <YAxis />
                <Tooltip formatter={(value) => `$${value.toLocaleString()}`} />
                <Bar dataKey="avgSalary" fill="#6366f1" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* Competency Matrix */}
          <ChartCard title="Competency Assessment" subtitle="Team competency levels vs benchmarks">
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={competencyData}>
                <PolarGrid />
                <PolarAngleAxis dataKey="subject" />
                <PolarRadiusAxis angle={90} domain={[0, 100]} />
                <Radar name="Current Team" dataKey="A" stroke="#6366f1" fill="#6366f1" fillOpacity={0.6} />
                <Radar name="Industry Benchmark" dataKey="B" stroke="#ec4899" fill="#ec4899" fillOpacity={0.6} />
                <Legend />
                <Tooltip />
              </RadarChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        {/* Summary Table */}
        <div className="bg-white rounded-xl p-6 border border-slate-200">
          <h3 className="font-bold text-lg mb-6">Department Performance Summary</h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b">
                <tr>
                  <th className="px-6 py-3 text-left font-medium text-slate-700">Department</th>
                  <th className="px-6 py-3 text-left font-medium text-slate-700">Headcount</th>
                  <th className="px-6 py-3 text-left font-medium text-slate-700">Avg Performance</th>
                  <th className="px-6 py-3 text-left font-medium text-slate-700">Utilization</th>
                  <th className="px-6 py-3 text-left font-medium text-slate-700">Turnover</th>
                  <th className="px-6 py-3 text-left font-medium text-slate-700">Trend</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { dept: 'Engineering', headcount: 235, perf: 92, util: 95, turn: 1.2, trend: 'up' },
                  { dept: 'Sales', headcount: 180, perf: 88, util: 92, turn: 2.5, trend: 'up' },
                  { dept: 'Marketing', headcount: 120, perf: 85, util: 90, turn: 3.1, trend: 'down' },
                  { dept: 'Operations', headcount: 95, perf: 87, util: 88, turn: 1.8, trend: 'up' },
                  { dept: 'HR', headcount: 45, perf: 89, util: 93, turn: 0.5, trend: 'stable' }
                ].map((row, i) => (
                  <tr key={i} className="border-b hover:bg-slate-50 transition">
                    <td className="px-6 py-4 font-medium">{row.dept}</td>
                    <td className="px-6 py-4">{row.headcount}</td>
                    <td className="px-6 py-4">{row.perf}%</td>
                    <td className="px-6 py-4">{row.util}%</td>
                    <td className="px-6 py-4">{row.turn}%</td>
                    <td className="px-6 py-4">
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                        row.trend === 'up' ? 'bg-green-100 text-green-700' :
                        row.trend === 'down' ? 'bg-red-100 text-red-700' :
                        'bg-blue-100 text-blue-700'
                      }`}>
                        {row.trend === 'up' && '↑ Improving'} {row.trend === 'down' && '↓ Declining'} {row.trend === 'stable' && '→ Stable'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* AI Insights */}
        <div className="mt-8 bg-gradient-to-r from-indigo-50 to-pink-50 rounded-xl p-6 border border-indigo-200">
          <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
            <span className="text-2xl">🤖</span> AI-Powered Insights
          </h3>
          <div className="grid md:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-slate-600 font-medium">Recommendation</p>
              <p className="text-slate-900 font-semibold mt-2">
                Engineering team utilization is high. Consider hiring 3-4 additional developers.
              </p>
            </div>
            <div>
              <p className="text-sm text-slate-600 font-medium">Alert</p>
              <p className="text-red-700 font-semibold mt-2">
                Marketing turnover increased 1.2% quarter-over-quarter. Review retention strategy.
              </p>
            </div>
            <div>
              <p className="text-sm text-slate-600 font-medium">Opportunity</p>
              <p className="text-green-700 font-semibold mt-2">
                Cross-training opportunity identified between Sales and Marketing teams.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
