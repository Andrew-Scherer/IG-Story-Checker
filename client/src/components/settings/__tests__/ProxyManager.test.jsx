import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ProxyManager from '../ProxyManager';

describe('ProxyManager', () => {
  const mockProps = {
    proxies: [
      {
        id: 1,
        host: '192.168.1.1',
        port: 8080,
        username: 'testuser',
        sessions: [
          {
            id: 1,
            session: 'test-session-data',
            status: 'active'
          }
        ],
        health: {
          status: 'healthy',
          latency: 150,
          uptime: 99.9,
          lastCheck: new Date().toISOString()
        }
      }
    ],
    onAdd: jest.fn(),
    onRemove: jest.fn(),
    onUpdate: jest.fn(),
    onTest: jest.fn(),
    onAddSession: jest.fn(),
    onRemoveSession: jest.fn(),
    onUpdateSession: jest.fn()
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Proxy Management', () => {
    it('should add a new proxy with valid input', async () => {
      render(<ProxyManager {...mockProps} />);
      
      const user = userEvent.setup();
      
      await act(async () => {
        await user.type(screen.getByLabelText(/host/i), '192.168.1.2');
        await user.type(screen.getByLabelText(/port/i), '8081');
        await user.type(screen.getByLabelText(/username/i), 'newuser');
        await user.click(screen.getByText('Add'));
      });
      
      expect(mockProps.onAdd).toHaveBeenCalledWith({
        host: '192.168.1.2',
        port: 8081,
        username: 'newuser'
      });
    });

    it('should validate IP address format', async () => {
      render(<ProxyManager {...mockProps} />);
      
      const user = userEvent.setup();
      
      await act(async () => {
        await user.type(screen.getByLabelText(/host/i), 'invalid-ip');
        await user.type(screen.getByLabelText(/port/i), '8081');
        await user.click(screen.getByText('Add'));
      });
      
      expect(screen.getByText('Invalid IP address')).toBeInTheDocument();
      expect(mockProps.onAdd).not.toHaveBeenCalled();
    });

    it('should validate port number range', async () => {
      render(<ProxyManager {...mockProps} />);
      
      const user = userEvent.setup();
      
      await act(async () => {
        await user.type(screen.getByLabelText(/host/i), '192.168.1.2');
        await user.type(screen.getByLabelText(/port/i), '99999');
        await user.click(screen.getByText('Add'));
      });
      
      expect(screen.getByText('Port must be between 1 and 65535')).toBeInTheDocument();
      expect(mockProps.onAdd).not.toHaveBeenCalled();
    });

    it('should remove a proxy after confirmation', async () => {
      render(<ProxyManager {...mockProps} />);
      
      const user = userEvent.setup();
      
      await act(async () => {
        await user.click(screen.getByTestId('remove-proxy-1'));
      });

      // Wait for modal to appear and click confirm
      const confirmButton = await screen.findByText('Confirm');
      await user.click(confirmButton);
      
      expect(mockProps.onRemove).toHaveBeenCalledWith(1);
    });
  });

  describe('Session Management', () => {
    it('should add a new session', async () => {
      render(<ProxyManager {...mockProps} />);
      
      const user = userEvent.setup();
      
      await act(async () => {
        await user.type(screen.getByPlaceholderText(/enter session data/i), 'new-session-data');
        await user.click(screen.getByText('Add Session'));
      });
      
      expect(mockProps.onAddSession).toHaveBeenCalledWith(1, {
        session: 'new-session-data'
      });
    });

    it('should validate empty session data', async () => {
      render(<ProxyManager {...mockProps} />);
      
      const user = userEvent.setup();
      
      await act(async () => {
        await user.click(screen.getByText('Add Session'));
      });
      
      expect(screen.getByText('Session data is required')).toBeInTheDocument();
      expect(mockProps.onAddSession).not.toHaveBeenCalled();
    });

    it('should toggle session status', async () => {
      render(<ProxyManager {...mockProps} />);
      
      const user = userEvent.setup();
      
      await act(async () => {
        await user.click(screen.getByText('active'));
      });
      
      expect(mockProps.onUpdateSession).toHaveBeenCalledWith(1, 1, {
        status: 'disabled'
      });
    });

    it('should update session data', async () => {
      render(<ProxyManager {...mockProps} />);
      
      const user = userEvent.setup();
      
      // Click edit button and wait for input to appear
      await user.click(screen.getByText('Edit'));
      const editInput = await screen.findByTestId('session-edit-1');
      
      // Type new content and save
      await user.type(editInput, '-updated');
      await user.click(screen.getByText('Save'));
      
      expect(mockProps.onUpdateSession).toHaveBeenCalledWith(1, 1, {
        session: 'test-session-data-updated'
      });
    });
  });

  describe('Health Monitoring', () => {
    it('should display health status indicators', () => {
      render(<ProxyManager {...mockProps} />);
      
      expect(screen.getByTestId('health-latency')).toHaveTextContent('150ms');
      expect(screen.getByTestId('health-uptime')).toHaveTextContent('99.9%');
      expect(screen.getByTestId('health-status')).toHaveTextContent('healthy');
    });

    it('should update health metrics display', async () => {
      const updatedProps = {
        ...mockProps,
        proxies: [{
          ...mockProps.proxies[0],
          health: {
            ...mockProps.proxies[0].health,
            latency: 200,
            uptime: 98.5
          }
        }]
      };
      
      const { rerender } = render(<ProxyManager {...mockProps} />);
      rerender(<ProxyManager {...updatedProps} />);
      
      expect(screen.getByTestId('health-latency')).toHaveTextContent('200ms');
      expect(screen.getByTestId('health-uptime')).toHaveTextContent('98.5%');
    });

    it('should highlight degraded performance', () => {
      const degradedProps = {
        ...mockProps,
        proxies: [{
          ...mockProps.proxies[0],
          health: {
            status: 'degraded',
            latency: 500,
            uptime: 85.5,
            lastCheck: new Date().toISOString()
          }
        }]
      };
      
      render(<ProxyManager {...degradedProps} />);
      
      const statusElement = screen.getByTestId('health-status');
      expect(statusElement).toHaveTextContent('degraded');
      expect(statusElement).toHaveClass('status-degraded');
      expect(screen.getByTestId('health-latency')).toHaveClass('latency-high');
    });
  });
});
