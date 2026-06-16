import React from 'react';

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, errorInfo: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true };
    }

    componentDidCatch(error, errorInfo) {
        console.error("ErrorBoundary caught an error", error, errorInfo);
        this.setState({ errorInfo });
    }

    render() {
        if (this.state.hasError) {
            return (
                <div style={{ padding: '40px', background: '#1f2937', color: '#f87171', borderRadius: '12px', textAlign: 'center', margin: '20px' }}>
                    <h2 style={{ marginBottom: '20px' }}>Something went wrong.</h2>
                    <p>The app encountered an unexpected error. Please refresh the page.</p>
                </div>
            );
        }

        return this.props.children; 
    }
}

export default ErrorBoundary;
