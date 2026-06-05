import React from 'react';
import { getAuthToken, clearAuthToken } from '../../services/api/authToken.js';
import { decodeJwtPayload } from './jwt.js';
import GateScreen from './GateScreen.jsx';
import TeamDashboard from './TeamDashboard.jsx';

class BusinessAdminErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error('Business admin dashboard crashed', error, info);
  }

  handleRetry = () => {
    this.setState({ error: null });
  };

  render() {
    if (!this.state.error) return this.props.children;
    const btn = {
      height: 36, padding: '0 16px', borderRadius: 10, border: '1px solid rgba(255,255,255,0.25)',
      background: 'rgba(255,255,255,0.06)', color: '#F4F5F7', fontSize: 13, fontWeight: 650, cursor: 'pointer',
    };
    return (
      <div style={{ minHeight: '100vh', background: '#0B0C10', color: '#F4F5F7',
        display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
        <div style={{ maxWidth: 460, textAlign: 'center' }}>
          <div style={{ fontSize: 11, letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.6)' }}>
            Matrix · Business admin
          </div>
          <h1 style={{ margin: '8px 0 6px', fontSize: 22, fontWeight: 720, letterSpacing: '-0.02em' }}>
            Approval center hit a display error
          </h1>
          <p style={{ margin: 0, fontSize: 13.5, color: 'rgba(255,255,255,0.7)', lineHeight: 1.55 }}>
            Refresh the view, or sign out and back in.
          </p>
          <div style={{ margin: '16px 0', padding: '10px 14px', borderRadius: 10, fontSize: 12.5,
            background: 'rgba(192,65,63,0.16)', color: '#F4A6A4', border: '1px solid rgba(192,65,63,0.4)' }}>
            {this.state.error?.message || 'Dashboard render failed.'}
          </div>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'center' }}>
            <button style={btn} type="button" onClick={this.handleRetry}>Refresh</button>
            <button style={btn} type="button" onClick={this.props.onLogout}>Sign out</button>
          </div>
        </div>
      </div>
    );
  }
}

export default function BusinessAdminPortalPage() {
  const [token, setToken] = React.useState(() => getAuthToken());
  const role = decodeJwtPayload(token).role;
  const logout = React.useCallback(() => {
    clearAuthToken();
    setToken(null);
  }, []);

  if (!token || role !== 'business_admin') {
    return <GateScreen onAuth={setToken}/>;
  }
  return (
    <BusinessAdminErrorBoundary key={token} onLogout={logout}>
      <TeamDashboard onLogout={logout}/>
    </BusinessAdminErrorBoundary>
  );
}
