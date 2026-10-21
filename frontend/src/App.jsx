import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./AuthContext.jsx";
import Layout from "./components/Layout.jsx";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Employees from "./pages/Employees.jsx";
import Departments from "./pages/Departments.jsx";
import Attendance from "./pages/Attendance.jsx";
import Leaves from "./pages/Leaves.jsx";
import Tasks from "./pages/Tasks.jsx";
import Assets from "./pages/Assets.jsx";
import Rooms from "./pages/Rooms.jsx";
import Announcements from "./pages/Announcements.jsx";
import Reports from "./pages/Reports.jsx";
import Profile from "./pages/Profile.jsx";

export default function App() {
  const { user, loading, canManage } = useAuth();

  if (loading) return <div className="center-screen">Đang tải...</div>;
  if (!user) {
    return (
      <Routes>
        <Route path="*" element={<Login />} />
      </Routes>
    );
  }

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/attendance" element={<Attendance />} />
        <Route path="/leaves" element={<Leaves />} />
        <Route path="/tasks" element={<Tasks />} />
        <Route path="/rooms" element={<Rooms />} />
        <Route path="/assets" element={<Assets />} />
        <Route path="/announcements" element={<Announcements />} />
        <Route path="/employees" element={<Employees />} />
        <Route path="/departments" element={<Departments />} />
        <Route path="/reports" element={canManage ? <Reports /> : <Navigate to="/" replace />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}
