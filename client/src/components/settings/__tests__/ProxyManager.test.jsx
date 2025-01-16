import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SettingsProxyManager from '../../settings/ProxyManager';
import TableProxyManager from '../../proxy/ProxyManager';
import useProxyStore from '../../../stores/proxyStore';

// Mock the store
jest.mock('../../../stores/proxyStore');

describe('ProxyManager Components', () => {
  describe('Settings Version (Form-based)', () => {
    const mockProxy = {
      id: 1,
      host: '192.168.1.1',
      port: 8080,
      username: 'user1',
      sessions: []
    };

    const mockProxyWithSession = {
      ...mockProxy,
      sessions: [
        {
          id: 1,
          session: 'test_session_123',
          status: 'active'
        }
      ]
    };

    const defaultProps = {
      proxies: [],
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

    it('renders empty state when no proxies', () => {
      render(<SettingsProxyManager {...defaultProps} />);
      expect(screen.getByText('No proxies configured')).toBeInTheDocument();
    });

    describe('Proxy Management', () => {
      it('adds a proxy with valid data', async () => {
        render(<SettingsProxyManager {...defaultProps} />);
        
        await userEvent.type(screen.getByLabelText('Host'), '192.168.1.1');
        await userEvent.type(screen.getByLabelText('Port'), '8080');
        await userEvent.type(screen.getByLabelText('Username (Optional)'), 'user1');
        
        fireEvent.click(screen.getByText('Add'));
        
        expect(defaultProps.onAdd).toHaveBeenCalledWith({
          host: '192.168.1.1',
          port: 8080,
          username: 'user1'
        });
      });

      it('shows validation errors for invalid proxy data', async () => {
        render(<SettingsProxyManager {...defaultProps} />);
        
        await userEvent.type(screen.getByLabelText('Host'), 'invalid');
        await userEvent.type(screen.getByLabelText('Port'), '99999');
        
        fireEvent.click(screen.getByText('Add'));
        
        expect(screen.getByText('Invalid IP address')).toBeInTheDocument();
        expect(screen.getByText('Port must be between 1 and 65535')).toBeInTheDocument();
        expect(defaultProps.onAdd).not.toHaveBeenCalled();
      });

      it('removes a proxy after confirmation', async () => {
        render(<SettingsProxyManager {...defaultProps} proxies={[mockProxy]} />);
        
        const removeButton = screen.getByText('Remove');
        fireEvent.click(removeButton);
        
        await waitFor(() => {
          expect(screen.getByText('Are you sure you want to remove this proxy?')).toBeInTheDocument();
        });
        
        const confirmButton = screen.getByText('Confirm');
        fireEvent.click(confirmButton);
        
        expect(defaultProps.onRemove).toHaveBeenCalledWith(mockProxy.id);
      });

      it('tests a proxy', async () => {
        defaultProps.onTest.mockResolvedValueOnce({ success: true, latency: 100 });
        
        render(<SettingsProxyManager {...defaultProps} proxies={[mockProxy]} />);
        
        const testButton = screen.getByText('Test');
        fireEvent.click(testButton);
        
        await waitFor(() => {
          expect(screen.getByText('100ms')).toBeInTheDocument();
        });
        
        expect(defaultProps.onTest).toHaveBeenCalledWith(mockProxy);
      });
    });

    describe('Session Management', () => {
      it('adds a session to a proxy', async () => {
        render(<SettingsProxyManager {...defaultProps} proxies={[mockProxy]} />);
        
        const sessionInput = screen.getByLabelText('Session Data');
        await userEvent.type(sessionInput, 'test_session_123');
        
        const addButton = screen.getByText('Add Session');
        fireEvent.click(addButton);
        
        expect(defaultProps.onAddSession).toHaveBeenCalledWith(
          mockProxy.id,
          { session: 'test_session_123' }
        );
      });

      it('shows validation error for empty session data', async () => {
        render(<SettingsProxyManager {...defaultProps} proxies={[mockProxy]} />);
        
        const addButton = screen.getByText('Add Session');
        fireEvent.click(addButton);
        
        expect(screen.getByText('Session data is required')).toBeInTheDocument();
        expect(defaultProps.onAddSession).not.toHaveBeenCalled();
      });

      it('removes a session from a proxy', async () => {
        render(<SettingsProxyManager {...defaultProps} proxies={[mockProxyWithSession]} />);
        
        const removeButtons = screen.getAllByText('Remove');
        const sessionRemoveButton = removeButtons[removeButtons.length - 1]; // Last remove button is for session
        fireEvent.click(sessionRemoveButton);
        
        await waitFor(() => {
          expect(defaultProps.onRemoveSession).toHaveBeenCalledWith(
            mockProxyWithSession.id,
            mockProxyWithSession.sessions[0].id
          );
        });
      });

      it('displays session status correctly', () => {
        render(<SettingsProxyManager {...defaultProps} proxies={[mockProxyWithSession]} />);
        
        expect(screen.getByText('active')).toBeInTheDocument();
        expect(screen.getByText('test_session_123')).toBeInTheDocument();
      });

      it('toggles session status', async () => {
        render(<SettingsProxyManager {...defaultProps} proxies={[mockProxyWithSession]} />);
        
        const statusButton = screen.getByText('active');
        fireEvent.click(statusButton);
        
        await waitFor(() => {
          expect(defaultProps.onUpdateSession).toHaveBeenCalledWith(
            mockProxyWithSession.id,
            mockProxyWithSession.sessions[0].id,
            { status: 'disabled' }
          );
        });
      });

      it('allows editing session data', async () => {
        render(<SettingsProxyManager {...defaultProps} proxies={[mockProxyWithSession]} />);
        
        // Enter edit mode
        const editButton = screen.getByText('Edit');
        fireEvent.click(editButton);
        
        // Find input and update value
        const input = screen.getByDisplayValue('test_session_123');
        await userEvent.clear(input);
        await userEvent.type(input, 'updated_session_456');
        
        // Save changes
        const saveButton = screen.getByText('Save');
        fireEvent.click(saveButton);
        
        await waitFor(() => {
          expect(defaultProps.onUpdateSession).toHaveBeenCalledWith(
            mockProxyWithSession.id,
            mockProxyWithSession.sessions[0].id,
            { session: 'updated_session_456' }
          );
        });
      });

      it('validates session data during editing', async () => {
        render(<SettingsProxyManager {...defaultProps} proxies={[mockProxyWithSession]} />);
        
        // Enter edit mode
        const editButton = screen.getByText('Edit');
        fireEvent.click(editButton);
        
        // Clear input (making it invalid)
        const input = screen.getByDisplayValue('test_session_123');
        await userEvent.clear(input);
        
        // Try to save
        fireEvent.click(screen.getByText('Save'));
        
        expect(screen.getByText('Session data is required')).toBeInTheDocument();
        expect(defaultProps.onUpdateSession).not.toHaveBeenCalled();
      });

      it('cancels session editing', async () => {
        render(<SettingsProxyManager {...defaultProps} proxies={[mockProxyWithSession]} />);
        
        // Enter edit mode
        const editButton = screen.getByText('Edit');
        fireEvent.click(editButton);
        
        // Update session data
        const input = screen.getByDisplayValue('test_session_123');
        await userEvent.clear(input);
        await userEvent.type(input, 'updated_session_456');
        
        // Cancel editing
        fireEvent.click(screen.getByText('Cancel'));
        
        // Original value should still be displayed
        expect(screen.getByText('test_session_123')).toBeInTheDocument();
        expect(defaultProps.onUpdateSession).not.toHaveBeenCalled();
      });
    });

    describe('Bulk Operations', () => {
      const mockProxies = [
        { ...mockProxy, id: 1 },
        { ...mockProxy, id: 2 }
      ];

      it('removes multiple selected proxies', async () => {
        render(<SettingsProxyManager {...defaultProps} proxies={mockProxies} />);
        
        // Select both proxies
        const checkboxes = screen.getAllByRole('checkbox');
        fireEvent.click(checkboxes[0]);
        fireEvent.click(checkboxes[1]);
        
        // Click remove selected
        fireEvent.click(screen.getByText('Remove Selected (2)'));
        
        await waitFor(() => {
          expect(screen.getByText('Are you sure you want to remove 2 selected proxies?')).toBeInTheDocument();
        });
        
        // Confirm removal in modal
        const confirmButton = screen.getByText('Confirm');
        fireEvent.click(confirmButton);
        
        expect(defaultProps.onRemove).toHaveBeenCalledWith([1, 2]);
      });
    });
  });

  describe('Table Version (Store-based)', () => {
    const mockStore = {
      proxies: [],
      addProxy: jest.fn(),
      removeProxy: jest.fn(),
      testProxy: jest.fn(),
      addSession: jest.fn(),
      updateSession: jest.fn()
    };

    beforeEach(() => {
      jest.clearAllMocks();
      useProxyStore.mockImplementation(() => mockStore);
    });

    it('renders table interface', () => {
      render(<TableProxyManager />);
      expect(screen.getByText('Proxy Management')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('ip:port:user:pass')).toBeInTheDocument();
    });

    it('adds single proxy with valid format', async () => {
      render(<TableProxyManager />);
      
      const input = screen.getByPlaceholderText('ip:port:user:pass');
      await userEvent.type(input, '192.168.1.1:8080:user1:pass1');
      fireEvent.click(screen.getByText('Add Proxy'));
      
      expect(mockStore.addProxy).toHaveBeenCalledWith({
        host: '192.168.1.1',
        port: '8080',
        username: 'user1',
        password: 'pass1',
        status: 'untested'
      });
    });

    it('validates proxy format before adding', async () => {
      const alertMock = jest.spyOn(window, 'alert').mockImplementation(() => {});
      render(<TableProxyManager />);
      
      const input = screen.getByPlaceholderText('ip:port:user:pass');
      await userEvent.type(input, 'invalid');
      fireEvent.click(screen.getByText('Add Proxy'));
      
      expect(alertMock).toHaveBeenCalledWith('Invalid proxy format. Use: ip:port:user:pass');
      expect(mockStore.addProxy).not.toHaveBeenCalled();
      
      alertMock.mockRestore();
    });

    it('adds multiple proxies with sessions', async () => {
      render(<TableProxyManager />);
      
      // Add proxies
      const proxyInput = screen.getByLabelText('Proxies (ip:port:username:password)');
      await userEvent.type(proxyInput, '192.168.1.1:8080:user1:pass1\n192.168.1.2:8080:user2:pass2');
      
      // Add sessions
      const sessionInput = screen.getByLabelText('Sessions (one per line)');
      await userEvent.type(sessionInput, 'session1\nsession2');
      
      // Add proxy-session pairs
      fireEvent.click(screen.getByText('Add Proxy-Session Pairs'));
      
      expect(mockStore.addProxy).toHaveBeenCalledTimes(2);
      expect(mockStore.addProxy).toHaveBeenCalledWith(expect.objectContaining({
        host: '192.168.1.1',
        port: 8080,
        username: 'user1',
        password: 'pass1'
      }));
      expect(mockStore.addProxy).toHaveBeenCalledWith(expect.objectContaining({
        host: '192.168.1.2',
        port: 8080,
        username: 'user2',
        password: 'pass2'
      }));
      
      expect(mockStore.addSession).toHaveBeenCalledTimes(2);
      expect(mockStore.addSession).toHaveBeenCalledWith(expect.any(Number), {
        session: 'session1',
        status: 'active'
      });
      expect(mockStore.addSession).toHaveBeenCalledWith(expect.any(Number), {
        session: 'session2',
        status: 'active'
      });
    });

    it('handles bulk operations on selected proxies', async () => {
      const mockProxies = [
        { id: 1, host: '192.168.1.1', port: '8080', username: 'user1', status: 'untested' },
        { id: 2, host: '192.168.1.2', port: '8080', username: 'user2', status: 'untested' }
      ];
      useProxyStore.mockImplementation(() => ({
        ...mockStore,
        proxies: mockProxies
      }));

      render(<TableProxyManager />);
      
      // Select proxies
      const checkboxes = screen.getAllByRole('checkbox');
      fireEvent.click(checkboxes[0]);
      fireEvent.click(checkboxes[1]);
      
      // Delete selected
      fireEvent.click(screen.getByText('Remove Selected (2)'));
      
      await waitFor(() => {
        expect(screen.getByText('Are you sure you want to remove 2 selected proxies?')).toBeInTheDocument();
      });
      
      // Confirm removal in modal
      const confirmButton = screen.getByText('Confirm');
      fireEvent.click(confirmButton);
      
      expect(mockStore.removeProxy).toHaveBeenCalledWith([1, 2]);
    });
  });
});
