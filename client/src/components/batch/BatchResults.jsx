import React, { useState, useMemo } from 'react';
import useNicheStore from '../../stores/nicheStore';
import useBatchStore from '../../stores/batchStore';
import Button from '../common/Button';
import Table from '../common/Table';
import './BatchResults.scss';

function BatchResults() {
  const { niches, selectedNicheId, setSelectedNicheId } = useNicheStore();
  const { 
    currentBatch,
    detections,
    runBatch,
    copyToClipboard,
    clearExpiredDetections
  } = useBatchStore();

  const [selectedIds, setSelectedIds] = useState([]);
  const [timeFilter, setTimeFilter] = useState('24h');

  // Auto-purge expired detections (older than 24h)
  React.useEffect(() => {
    const interval = setInterval(clearExpiredDetections, 60000); // Check every minute
    return () => clearInterval(interval);
  }, [clearExpiredDetections]);

  const handleNicheClick = (id) => {
    setSelectedNicheId(id === selectedNicheId ? null : id);
  };

  const handleRunBatch = () => {
    if (selectedNicheId) {
      runBatch(selectedNicheId);
    }
  };

  const handleCopySelected = () => {
    if (selectedIds.length > 0) {
      const usernames = filteredDetections
        .filter(detection => selectedIds.includes(detection.id))
        .map(detection => detection.username);
      copyToClipboard(usernames);
    }
  };

  const filteredDetections = useMemo(() => {
    if (!selectedNicheId) return [];
    
    const now = new Date();
    const cutoff = new Date(now - 24 * 60 * 60 * 1000); // 24 hours ago
    
    return detections.filter(detection => {
      if (detection.nicheId !== selectedNicheId) return false;
      const detectionTime = new Date(detection.detectedAt);
      return detectionTime > cutoff;
    });
  }, [selectedNicheId, detections]);

  const columns = [
    {
      key: 'username',
      title: 'Username',
      sortable: true,
      render: (detection) => (
        <a 
          href={`https://instagram.com/${detection.username}`}
          target="_blank"
          rel="noopener noreferrer"
        >
          {detection.username}
        </a>
      )
    },
    {
      key: 'detectedAt',
      title: 'Detected',
      sortable: true,
      render: (detection) => {
        const date = new Date(detection.detectedAt);
        return date.toLocaleString();
      }
    }
  ];

  return (
    <div className="batch-results">
      <div className="batch-results__sidebar">
        <div className="batch-results__niches">
          {niches.map(niche => (
            <div
              key={niche.id}
              className={`batch-results__niche ${
                selectedNicheId === niche.id ? 'batch-results__niche--selected' : ''
              }`}
              onClick={() => handleNicheClick(niche.id)}
            >
              <span className="batch-results__niche-name">{niche.name}</span>
              <span className="batch-results__niche-count">
                {filteredDetections.length} active
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="batch-results__content">
        {selectedNicheId && (
          <div className="batch-results__batch">
            <div className="batch-results__batch-info">
              {currentBatch?.nicheId === selectedNicheId ? (
                <span>Processing: {currentBatch.current}/{currentBatch.total}</span>
              ) : (
                <span>Batch idle</span>
              )}
            </div>
            <Button 
              onClick={handleRunBatch}
              disabled={currentBatch?.nicheId === selectedNicheId}
            >
              Run Batch Now
            </Button>
          </div>
        )}

        <div className="batch-results__detections">
          <div className="batch-results__header">
            <h2>Story Detections</h2>
            {selectedIds.length > 0 && (
              <Button onClick={handleCopySelected}>
                Copy {selectedIds.length} Username{selectedIds.length !== 1 ? 's' : ''}
              </Button>
            )}
          </div>

          {!selectedNicheId ? (
            <div className="batch-results__empty">
              <p>Select a niche to view detections</p>
            </div>
          ) : !filteredDetections.length ? (
            <div className="batch-results__empty">
              <p>No active stories detected</p>
            </div>
          ) : (
            <Table
              data={filteredDetections}
              columns={columns}
              pageSize={100}
              selectable={true}
              selectedRows={selectedIds}
              onSelectionChange={setSelectedIds}
            />
          )}
        </div>
      </div>
    </div>
  );
}

export default BatchResults;
