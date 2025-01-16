import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ProxyManager from '../ProxyManager';

describe('ProxyManager Component', () => {
  const mockProxies = [
    { id: 1, host: '192.168.1.1', port: 8080 },
    { id: 2, host: '192.168.1.2', port: 8081 }
  ];

  const defaultProps = {
    proxies: mockProxies,
    onAdd: jest.fn(),
    onRemove: jest.fn(),
    onUpdate: jest.fn()
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Proxy List Display', () => {
    it('renders all proxies with their details', () => {
      render(<ProxyManager {...defaultProps} />);

      mockProxies.forEach(proxy => {
        expect(screen.getByText(`${proxy.host}:${proxy.port}`)).toBeInTheDocument();
      });
    });

    it('shows empty state when no proxies exist', () => {
      render(<ProxyManager {...defaultProps} proxies={[]} />);
      expect(screen.getByText(/no proxies configured/i)).toBeInTheDocument();
    });
  });

  describe('Proxy Addition', () => {
    it('adds a valid proxy', () => {
      render(<ProxyManager {...defaultProps} />);
      
      fireEvent.change(screen.getByLabelText(/host/i), {
        target: { value: '192.168.1.3' }
      });
      fireEvent.change(screen.getByLabelText(/port/i), {
        target: { value: '8082' }
      });
      
      fireEvent.click(screen.getByRole('button', { name: /add/i }));
      
      expect(defaultProps.onAdd).toHaveBeenCalledWith({
        host: '192.168.1.3',
        port: 8082
      });
    });

    it('validates IP address format', () => {
      render(<ProxyManager {...defaultProps} />);
      
      fireEvent.change(screen.getByLabelText(/host/i), {
        target: { value: 'invalid-ip' }
      });
      fireEvent.change(screen.getByLabelText(/port/i), {
        target: { value: '8082' }
      });
      
      fireEvent.click(screen.getByRole('button', { name: /add/i }));
      
      expect(screen.getByText(/invalid ip address/i)).toBeInTheDocument();
      expect(defaultProps.onAdd).not.toHaveBeenCalled();
    });

    it('validates port number range', () => {
      render(<ProxyManager {...defaultProps} />);
      
      fireEvent.change(screen.getByLabelText(/host/i), {
        target: { value: '192.168.1.3' }
      });
      fireEvent.change(screen.getByLabelText(/port/i), {
        target: { value: '99999' }
      });
      
      fireEvent.click(screen.getByRole('button', { name: /add/i }));
      
      expect(screen.getByText(/port must be between 1 and 65535/i)).toBeInTheDocument();
      expect(defaultProps.onAdd).not.toHaveBeenCalled();
    });

    it('prevents duplicate proxy entries', () => {
      render(<ProxyManager {...defaultProps} />);
      
      fireEvent.change(screen.getByLabelText(/host/i), {
        target: { value: '192.168.1.1' }
      });
      fireEvent.change(screen.getByLabelText(/port/i), {
        target: { value: '8080' }
      });
      
      fireEvent.click(screen.getByRole('button', { name: /add/i }));
      
      expect(screen.getByText(/proxy already exists/i)).toBeInTheDocument();
      expect(defaultProps.onAdd).not.toHaveBeenCalled();
    });
  });

  describe('Proxy Removal', () => {
    it('removes a single proxy', async () => {
      render(<ProxyManager {...defaultProps} />);
      
      const removeButtons = screen.getAllByRole('button', { name: /remove/i });
      fireEvent.click(removeButtons[0]);

      // Confirm removal
      const confirmButton = screen.getByRole('button', { name: /confirm/i });
      fireEvent.click(confirmButton);
      
      expect(defaultProps.onRemove).toHaveBeenCalledWith(mockProxies[0].id);
    });

    it('removes multiple selected proxies', () => {
      render(<ProxyManager {...defaultProps} />);
      
      const checkboxes = screen.getAllByRole('checkbox');
      fireEvent.click(checkboxes[0]); // First proxy
      fireEvent.click(checkboxes[1]); // Second proxy
      
      fireEvent.click(screen.getByRole('button', { name: /remove selected/i }));
      
      expect(defaultProps.onRemove).toHaveBeenCalledWith([
        mockProxies[0].id,
        mockProxies[1].id
      ]);
    });

    it('shows confirmation dialog before removing proxies', () => {
      render(<ProxyManager {...defaultProps} />);
      
      const removeButtons = screen.getAllByRole('button', { name: /remove/i });
      fireEvent.click(removeButtons[0]);
      
      expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
      expect(screen.getByText(/this action cannot be undone/i)).toBeInTheDocument();
      
      fireEvent.click(screen.getByRole('button', { name: /confirm/i }));
      expect(defaultProps.onRemove).toHaveBeenCalledWith(mockProxies[0].id);
    });
  });

  describe('Authentication', () => {
    it('supports optional username and password', () => {
      render(<ProxyManager {...defaultProps} />);
      
      fireEvent.change(screen.getByLabelText(/host/i), {
        target: { value: '192.168.1.3' }
      });
      fireEvent.change(screen.getByLabelText(/port/i), {
        target: { value: '8082' }
      });
      fireEvent.change(screen.getByLabelText(/username/i), {
        target: { value: 'user' }
      });
      fireEvent.change(screen.getByLabelText(/password/i), {
        target: { value: 'pass' }
      });
      
      fireEvent.click(screen.getByRole('button', { name: /add/i }));
      
      expect(defaultProps.onAdd).toHaveBeenCalledWith({
        host: '192.168.1.3',
        port: 8082,
        username: 'user',
        password: 'pass'
      });
    });

    it('validates authentication format', () => {
      render(<ProxyManager {...defaultProps} />);
      
      fireEvent.change(screen.getByLabelText(/host/i), {
        target: { value: '192.168.1.3' }
      });
      fireEvent.change(screen.getByLabelText(/port/i), {
        target: { value: '8082' }
      });
      fireEvent.change(screen.getByLabelText(/username/i), {
        target: { value: 'user@' }
      });
      
      fireEvent.click(screen.getByRole('button', { name: /add/i }));
      
      expect(screen.getByText(/invalid username format/i)).toBeInTheDocument();
      expect(defaultProps.onAdd).not.toHaveBeenCalled();
    });
  });

  describe('Proxy Testing', () => {
    it('tests proxy connection', async () => {
      const onTest = jest.fn().mockResolvedValue({ success: true, latency: 100 });
      render(<ProxyManager {...defaultProps} onTest={onTest} />);
      
      const testButtons = screen.getAllByRole('button', { name: /test/i });
      fireEvent.click(testButtons[0]);
      
      expect(await screen.findByText(/100ms/i)).toBeInTheDocument();
      expect(onTest).toHaveBeenCalledWith(mockProxies[0]);
    });

    it('shows error on failed proxy test', async () => {
      const onTest = jest.fn().mockRejectedValue(new Error('Connection failed'));
      render(<ProxyManager {...defaultProps} onTest={onTest} />);
      
      const testButtons = screen.getAllByRole('button', { name: /test/i });
      fireEvent.click(testButtons[0]);
      
      expect(await screen.findByText(/connection failed/i)).toBeInTheDocument();
      expect(onTest).toHaveBeenCalledWith(mockProxies[0]);
    });
  });
});
