"""
Database layer for identity circuit factory.
Handles storage, retrieval, and management of circuits and their relationships.
Supports debris cancellation, job queue management, and ML feature extraction.
"""

import sqlite3
import json
import hashlib
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import logging
from datetime import datetime
import pickle
import base64

logger = logging.getLogger(__name__)

@dataclass
class CircuitRecord:
    """Represents a circuit stored in the database."""
    id: Optional[int]
    width: int
    gate_count: int  # This is the length in gates
    gates: List[Tuple]
    permutation: List[int]
    complexity_walk: Optional[List[int]] = None
    circuit_hash: Optional[str] = None
    dim_group_id: Optional[int] = None  # Added to fix attribute access issues
    representative_id: Optional[int] = None  # Points to representative circuit (self if representative)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'width': self.width,
            'gate_count': self.gate_count,
            'gates': self.gates,
            'permutation': self.permutation,
            'complexity_walk': self.complexity_walk,
            'circuit_hash': self.circuit_hash,
            'dim_group_id': self.dim_group_id,
            'representative_id': self.representative_id
        }

@dataclass
class DimGroupRecord:
    """Represents a dimension group - a collection of identity circuits with same (width, gate_count)."""
    id: Optional[int]
    width: int
    gate_count: int  # Number of gates in the circuits
    circuit_count: int = 0  # How many circuits are in this dim group
    is_processed: bool = False  # Whether unrolling has been done
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'width': self.width,
            'gate_count': self.gate_count,
            'circuit_count': self.circuit_count,
            'is_processed': self.is_processed
        }

@dataclass
class RepresentativeRecord:
    """Represents a representative circuit within a dimension group."""
    id: Optional[int]
    dim_group_id: int
    circuit_id: int  # The actual representative circuit
    gate_composition: Tuple[int, int, int]  # (n1, n2, n3) - NOT, CNOT, CCNOT counts
    is_primary: bool = False  # Whether this is the primary representative
    fully_unrolled: bool = False  # Whether this representative has been fully unrolled
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'dim_group_id': self.dim_group_id,
            'circuit_id': self.circuit_id,
            'gate_composition': self.gate_composition,
            'is_primary': self.is_primary,
            'fully_unrolled': self.fully_unrolled
        }

@dataclass
class EquivalentRecord:
    """Represents an equivalent circuit generated from a representative."""
    id: Optional[int]
    circuit_id: int
    representative_id: int  # Points to the representative this was unrolled from
    unroll_type: Optional[str] = None
    unroll_params: Optional[Dict] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'circuit_id': self.circuit_id,
            'representative_id': self.representative_id,
            'unroll_type': self.unroll_type,
            'unroll_params': self.unroll_params
        }

@dataclass
class DebrisCancellationRecord:
    """Represents debris cancellation analysis results."""
    id: Optional[int]
    circuit_id: int
    dim_group_id: int
    debris_gates: List[Tuple]  # Gates inserted as debris
    cancellation_path: List[int]  # Sequence of gate indices in cancellation
    non_triviality_score: float  # Difficulty of cancellation
    final_gate_count: int
    cancellation_metrics: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'circuit_id': self.circuit_id,
            'dim_group_id': self.dim_group_id,
            'debris_gates': self.debris_gates,
            'cancellation_path': self.cancellation_path,
            'non_triviality_score': self.non_triviality_score,
            'final_gate_count': self.final_gate_count,
            'cancellation_metrics': self.cancellation_metrics
        }

@dataclass
class JobRecord:
    """Represents a job in the processing queue."""
    id: Optional[int]
    job_type: str  # 'seed_generation', 'unrolling', 'post_processing', 'debris_analysis'
    status: str  # 'pending', 'running', 'completed', 'failed'
    priority: int
    parameters: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'job_type': self.job_type,
            'status': self.status,
            'priority': self.priority,
            'parameters': self.parameters,
            'result': self.result,
            'error_message': self.error_message,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at
        }

@dataclass
class MLFeatureRecord:
    """Represents ML features extracted from circuits."""
    id: Optional[int]
    circuit_id: int
    dim_group_id: int
    features: Dict[str, float]  # Feature name -> value
    complexity_prediction: Optional[float] = None
    optimization_suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'circuit_id': self.circuit_id,
            'dim_group_id': self.dim_group_id,
            'features': self.features,
            'complexity_prediction': self.complexity_prediction,
            'optimization_suggestion': self.optimization_suggestion
        }

class CircuitDatabase:
    """Database manager for identity circuit factory."""
    
    def __init__(self, db_path: str = "identity_circuits.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables with correct schema."""
        with sqlite3.connect(self.db_path) as conn:
            # Core circuit table - stores all identity circuits
            conn.execute("""
                CREATE TABLE IF NOT EXISTS circuits (
                    id INTEGER PRIMARY KEY,
                    width INTEGER NOT NULL,
                    gate_count INTEGER NOT NULL,
                    gates TEXT NOT NULL,
                    permutation TEXT NOT NULL,
                    complexity_walk TEXT,
                    circuit_hash TEXT UNIQUE,
                    representative_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (representative_id) REFERENCES circuits(id)
                )
            """)
            
            # Dimension groups - collections of circuits with same (width, gate_count)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS dim_groups (
                    id INTEGER PRIMARY KEY,
                    width INTEGER NOT NULL,
                    gate_count INTEGER NOT NULL,
                    circuit_count INTEGER DEFAULT 0,
                    is_processed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(width, gate_count)
                )
            """)
            
            # Dimension group membership - which circuits belong to which dim groups
            conn.execute("""
                CREATE TABLE IF NOT EXISTS dim_group_circuits (
                    id INTEGER PRIMARY KEY,
                    dim_group_id INTEGER NOT NULL,
                    circuit_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (dim_group_id) REFERENCES dim_groups(id),
                    FOREIGN KEY (circuit_id) REFERENCES circuits(id),
                    UNIQUE(dim_group_id, circuit_id)
                )
            """)
            
            # Representatives - specific circuits chosen as representatives for gate compositions
            conn.execute("""
                CREATE TABLE IF NOT EXISTS representatives (
                    id INTEGER PRIMARY KEY,
                    dim_group_id INTEGER NOT NULL,
                    circuit_id INTEGER NOT NULL,
                    gate_composition TEXT NOT NULL,  -- JSON of (n1, n2, n3)
                    is_primary BOOLEAN DEFAULT FALSE,
                    fully_unrolled BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (dim_group_id) REFERENCES dim_groups(id),
                    FOREIGN KEY (circuit_id) REFERENCES circuits(id)
                )
            """)
            
            # Equivalents - circuits generated by unrolling representatives
            conn.execute("""
                CREATE TABLE IF NOT EXISTS equivalents (
                    id INTEGER PRIMARY KEY,
                    circuit_id INTEGER NOT NULL,
                    representative_id INTEGER NOT NULL,
                    unroll_type TEXT,
                    unroll_params TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (circuit_id) REFERENCES circuits(id),
                    FOREIGN KEY (representative_id) REFERENCES representatives(id)
                )
            """)
            
            # Simplifications - basic swap and cancellation results
            conn.execute("""
                CREATE TABLE IF NOT EXISTS simplifications (
                    id INTEGER PRIMARY KEY,
                    original_circuit_id INTEGER NOT NULL,
                    simplified_circuit_id INTEGER,
                    target_dim_group_id INTEGER,
                    reduction_metrics TEXT,
                    simplification_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (original_circuit_id) REFERENCES circuits(id),
                    FOREIGN KEY (simplified_circuit_id) REFERENCES circuits(id),
                    FOREIGN KEY (target_dim_group_id) REFERENCES dim_groups(id)
                )
            """)
            
            # Debris cancellation analysis
            conn.execute("""
                CREATE TABLE IF NOT EXISTS debris_cancellations (
                    id INTEGER PRIMARY KEY,
                    circuit_id INTEGER NOT NULL,
                    dim_group_id INTEGER NOT NULL,
                    debris_gates TEXT NOT NULL,
                    cancellation_path TEXT NOT NULL,
                    non_triviality_score REAL NOT NULL,
                    final_gate_count INTEGER NOT NULL,
                    cancellation_metrics TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (circuit_id) REFERENCES circuits(id),
                    FOREIGN KEY (dim_group_id) REFERENCES dim_groups(id)
                )
            """)
            
            # Job queue for distributed processing
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY,
                    job_type TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    priority INTEGER DEFAULT 0,
                    parameters TEXT NOT NULL,
                    result TEXT,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)
            
            # ML features and predictions
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ml_features (
                    id INTEGER PRIMARY KEY,
                    circuit_id INTEGER NOT NULL,
                    dim_group_id INTEGER NOT NULL,
                    features TEXT NOT NULL,
                    complexity_prediction REAL,
                    optimization_suggestion TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (circuit_id) REFERENCES circuits(id),
                    FOREIGN KEY (dim_group_id) REFERENCES dim_groups(id)
                )
            """)
            
            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_circuits_dim ON circuits(width, gate_count)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_circuits_hash ON circuits(circuit_hash)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_dim_group_circuits ON dim_group_circuits(dim_group_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_representatives_dim_group ON representatives(dim_group_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_representatives_composition ON representatives(gate_composition)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_equivalents_circuit ON equivalents(circuit_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_equivalents_representative ON equivalents(representative_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status, priority)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_type ON jobs(job_type, status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ml_features_circuit ON ml_features(circuit_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ml_features_dim_group ON ml_features(dim_group_id)")
            
            conn.commit()
    
    def _compute_circuit_hash(self, gates: List[Tuple], permutation: List[int]) -> str:
        """Compute a hash for circuit identity."""
        try:
            # Convert gates and permutation to JSON strings for consistent hashing
            gates_str = json.dumps(gates, sort_keys=True)
            permutation_str = json.dumps(permutation, sort_keys=True)
            circuit_data = gates_str + permutation_str
            return hashlib.sha256(circuit_data.encode()).hexdigest()
        except (TypeError, json.JSONEncodeError) as e:
            logger.warning(f"Failed to compute circuit hash: {e}")
            # Fallback to string representation
            circuit_data = str(gates) + str(permutation)
            return hashlib.sha256(circuit_data.encode()).hexdigest()
    
    def store_circuit(self, circuit: CircuitRecord) -> int:
        """Store a circuit and return its ID."""
        if circuit.circuit_hash is None:
            circuit.circuit_hash = self._compute_circuit_hash(circuit.gates, circuit.permutation)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT OR IGNORE INTO circuits (width, gate_count, gates, permutation, complexity_walk, circuit_hash, representative_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                circuit.width,
                circuit.gate_count,
                json.dumps(circuit.gates),
                json.dumps(circuit.permutation),
                json.dumps(circuit.complexity_walk) if circuit.complexity_walk else None,
                circuit.circuit_hash,
                circuit.representative_id
            ))
            
            if cursor.lastrowid == 0:
                # Circuit already exists, get its ID
                cursor = conn.execute("SELECT id FROM circuits WHERE circuit_hash = ?", (circuit.circuit_hash,))
                return cursor.fetchone()[0]
            return cursor.lastrowid
    
    def get_circuit(self, circuit_id: int) -> Optional[CircuitRecord]:
        """Retrieve a circuit by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT c.id, c.width, c.gate_count, c.gates, c.permutation, c.complexity_walk, c.circuit_hash,
                       dgc.dim_group_id, c.representative_id
                FROM circuits c
                LEFT JOIN dim_group_circuits dgc ON c.id = dgc.circuit_id
                WHERE c.id = ?
            """, (circuit_id,))
            row = cursor.fetchone()
            
            if row:
                try:
                    return CircuitRecord(
                        id=row[0],
                        width=row[1],
                        gate_count=row[2],
                        gates=json.loads(row[3]) if row[3] is not None else [],
                        permutation=json.loads(row[4]) if row[4] is not None else list(range(row[1])),
                        complexity_walk=json.loads(row[5]) if row[5] is not None else None,
                        circuit_hash=row[6],
                        dim_group_id=row[7],
                        representative_id=row[8]
                    )
                except (json.JSONDecodeError, TypeError) as e:
                    logger.error(f"Failed to parse circuit {circuit_id} data: {e}")
                    return None
            return None
    
    def get_circuit_by_hash(self, circuit_hash: str) -> Optional[CircuitRecord]:
        """Retrieve a circuit by its hash."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT c.id, c.width, c.gate_count, c.gates, c.permutation, c.complexity_walk, c.circuit_hash,
                       dgc.dim_group_id
                FROM circuits c
                LEFT JOIN dim_group_circuits dgc ON c.id = dgc.circuit_id
                WHERE c.circuit_hash = ?
            """, (circuit_hash,))
            row = cursor.fetchone()
            
            if row:
                return CircuitRecord(
                    id=row[0],
                    width=row[1],
                    gate_count=row[2],
                    gates=json.loads(row[3]),
                    permutation=json.loads(row[4]),
                    complexity_walk=json.loads(row[5]) if row[5] else None,
                    circuit_hash=row[6],
                    dim_group_id=row[7]
                )
            return None
    
    def store_dim_group(self, dim_group: DimGroupRecord) -> int:
        """Store a dimension group and return its ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO dim_groups 
                (width, gate_count, circuit_count, is_processed)
                VALUES (?, ?, ?, ?)
            """, (
                dim_group.width,
                dim_group.gate_count,
                dim_group.circuit_count,
                dim_group.is_processed
            ))
            return cursor.lastrowid
    
    def get_dim_group(self, width: int, gate_count: int) -> Optional[DimGroupRecord]:
        """Get dimension group by width and gate_count."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, width, gate_count, circuit_count, is_processed
                FROM dim_groups WHERE width = ? AND gate_count = ?
            """, (width, gate_count))
            row = cursor.fetchone()
            
            if row:
                return DimGroupRecord(
                    id=row[0],
                    width=row[1],
                    gate_count=row[2],
                    circuit_count=row[3],
                    is_processed=bool(row[4])
                )
            return None
    
    def get_dim_group_by_id(self, dim_group_id: int) -> Optional[DimGroupRecord]:
        """Get dimension group by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, width, gate_count, circuit_count, is_processed
                FROM dim_groups WHERE id = ?
            """, (dim_group_id,))
            row = cursor.fetchone()
            
            if row:
                return DimGroupRecord(
                    id=row[0],
                    width=row[1],
                    gate_count=row[2],
                    circuit_count=row[3],
                    is_processed=bool(row[4])
                )
            return None
    
    def add_circuit_to_dim_group(self, dim_group_id: int, circuit_id: int) -> int:
        """Add a circuit to a dimension group."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT OR IGNORE INTO dim_group_circuits (dim_group_id, circuit_id)
                VALUES (?, ?)
            """, (dim_group_id, circuit_id))
            
            # Update circuit count
            conn.execute("""
                UPDATE dim_groups SET circuit_count = (
                    SELECT COUNT(*) FROM dim_group_circuits WHERE dim_group_id = ?
                ) WHERE id = ?
            """, (dim_group_id, dim_group_id))
            
            return cursor.lastrowid
    
    def get_circuits_in_dim_group(self, dim_group_id: int) -> List[CircuitRecord]:
        """Get all circuits in a dimension group."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT c.id, c.width, c.gate_count, c.gates, c.permutation, c.complexity_walk, c.circuit_hash, c.representative_id
                FROM circuits c
                JOIN dim_group_circuits dgc ON c.id = dgc.circuit_id
                WHERE dgc.dim_group_id = ?
                ORDER BY c.id
            """, (dim_group_id,))
            
            circuits = []
            for row in cursor.fetchall():
                try:
                    circuits.append(CircuitRecord(
                        id=row[0],
                        width=row[1], 
                        gate_count=row[2],
                        gates=json.loads(row[3]) if row[3] is not None else [],
                        permutation=json.loads(row[4]) if row[4] is not None else list(range(row[1])),
                        complexity_walk=json.loads(row[5]) if row[5] is not None else None,
                        circuit_hash=row[6],
                        dim_group_id=dim_group_id,
                        representative_id=row[7]
                    ))
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Failed to parse circuit {row[0]} in dim group {dim_group_id}: {e}")
                    continue
            
            return circuits

    def get_circuit_dim_group(self, circuit_id: int) -> Optional[int]:
        """Get the dimension group ID for a circuit."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT dim_group_id FROM dim_group_circuits WHERE circuit_id = ?
            """, (circuit_id,))
            row = cursor.fetchone()
            return row[0] if row else None
    
    def store_representative(self, rep: RepresentativeRecord) -> int:
        """Store a representative and return its ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO representatives (dim_group_id, circuit_id, gate_composition, is_primary, fully_unrolled)
                VALUES (?, ?, ?, ?, ?)
            """, (
                rep.dim_group_id,
                rep.circuit_id,
                json.dumps(rep.gate_composition),
                rep.is_primary,
                rep.fully_unrolled
            ))
            return cursor.lastrowid
    
    def get_representatives_for_dim_group(self, dim_group_id: int) -> List[RepresentativeRecord]:
        """Get all representatives for a dimension group."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, dim_group_id, circuit_id, gate_composition, is_primary, fully_unrolled
                FROM representatives WHERE dim_group_id = ?
            """, (dim_group_id,))
            
            return [
                RepresentativeRecord(
                    id=row[0],
                    dim_group_id=row[1],
                    circuit_id=row[2],
                    gate_composition=tuple(json.loads(row[3])),
                    is_primary=bool(row[4]),
                    fully_unrolled=bool(row[5])
                )
                for row in cursor.fetchall()
            ]
    
    def get_representative_by_composition(self, dim_group_id: int, gate_composition: Tuple[int, int, int]) -> Optional[RepresentativeRecord]:
        """Get a representative by its gate composition within a dimension group."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, dim_group_id, circuit_id, gate_composition, is_primary, fully_unrolled
                FROM representatives WHERE dim_group_id = ? AND gate_composition = ?
            """, (dim_group_id, json.dumps(gate_composition)))
            row = cursor.fetchone()
            
            if row:
                return RepresentativeRecord(
                    id=row[0],
                    dim_group_id=row[1],
                    circuit_id=row[2],
                    gate_composition=tuple(json.loads(row[3])),
                    is_primary=bool(row[4]),
                    fully_unrolled=bool(row[5])
                )
            return None
    
    def get_representatives_by_composition(self, dim_group_id: int, gate_composition: Tuple[int, int, int]) -> List[RepresentativeRecord]:
        """Get ALL representatives by gate composition within a dimension group."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, dim_group_id, circuit_id, gate_composition, is_primary, fully_unrolled
                FROM representatives WHERE dim_group_id = ? AND gate_composition = ?
                ORDER BY id
            """, (dim_group_id, json.dumps(gate_composition)))
            
            representatives = []
            for row in cursor.fetchall():
                representatives.append(RepresentativeRecord(
                    id=row[0],
                    dim_group_id=row[1],
                    circuit_id=row[2],
                    gate_composition=tuple(json.loads(row[3])),
                    is_primary=bool(row[4]),
                    fully_unrolled=bool(row[5])
                ))
            return representatives
    
    def store_equivalent(self, equiv: EquivalentRecord) -> int:
        """Store an equivalent circuit relationship."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO equivalents 
                (circuit_id, representative_id, unroll_type, unroll_params)
                VALUES (?, ?, ?, ?)
            """, (
                equiv.circuit_id,
                equiv.representative_id,
                equiv.unroll_type,
                json.dumps(equiv.unroll_params) if equiv.unroll_params else None
            ))
            return cursor.lastrowid
    
    def get_equivalents_for_representative(self, representative_id: int) -> List[Dict[str, Any]]:
        """Get all circuit equivalents for a representative."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT e.circuit_id, e.unroll_type, e.unroll_params,
                       c.width, c.gate_count, c.gates, c.permutation
                FROM equivalents e
                JOIN circuits c ON e.circuit_id = c.id
                WHERE e.representative_id = ?
            """, (representative_id,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'circuit_id': row[0],
                    'unroll_type': row[1],
                    'unroll_params': json.loads(row[2]) if row[2] else None,
                    'width': row[3],
                    'gate_count': row[4],
                    'gates': json.loads(row[5]),
                    'permutation': json.loads(row[6])
                })
            return results
    
    def get_equivalents_for_dim_group(self, dim_group_id: int) -> List[Dict[str, Any]]:
        """Get all equivalents for circuits in a dimension group (alias for compatibility)."""
        return self.get_all_equivalents_for_dim_group(dim_group_id)
    
    def get_all_equivalents_for_dim_group(self, dim_group_id: int) -> List[Dict[str, Any]]:
        """Get all equivalent circuits for a dimension group."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT c.*, e.unroll_type, e.unroll_params
                FROM circuits c
                JOIN equivalents e ON c.id = e.circuit_id
                JOIN representatives r ON e.representative_id = r.circuit_id
                WHERE r.dim_group_id = ?
                ORDER BY c.id
            """, (dim_group_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_equivalent_count_for_dim_group(self, dim_group_id: int) -> int:
        """Get the total count of equivalent circuits for a dimension group."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT COUNT(*)
                FROM equivalents e
                JOIN representatives r ON e.representative_id = r.circuit_id
                WHERE r.dim_group_id = ?
            """, (dim_group_id,))
            return cursor.fetchone()[0]

    def get_equivalents_for_circuit(self, circuit_id: int) -> List[CircuitRecord]:
        """Get all equivalent circuits for a given circuit."""
        with sqlite3.connect(self.db_path) as conn:
            # Get the representative_id for this circuit
            cursor = conn.execute("SELECT representative_id FROM circuits WHERE id = ?", (circuit_id,))
            row = cursor.fetchone()
            
            if not row or not row[0]:
                return []
            
            representative_id = row[0]
            
            # Get all circuits that have this representative_id (excluding the representative itself)
            cursor = conn.execute("""
                SELECT id, width, gate_count, gates, permutation, complexity_walk, representative_id
                FROM circuits 
                WHERE representative_id = ? AND id != ?
            """, (representative_id, representative_id))
            
            equivalents = []
            for row in cursor.fetchall():
                try:
                    record = CircuitRecord(
                        id=row[0],
                        width=row[1],
                        gate_count=row[2],
                        gates=json.loads(row[3]) if row[3] is not None else [],
                        permutation=json.loads(row[4]) if row[4] is not None else list(range(row[1])),
                        complexity_walk=json.loads(row[5]) if row[5] is not None else None,
                        representative_id=row[6]
                    )
                    equivalents.append(record)
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Failed to parse circuit {row[0]} data: {e}")
                    continue
            
            return equivalents

    def store_equivalent_circuit(self, original_circuit_id: int, gates: List[Tuple], 
                               width: int, permutation: List[int],
                               unroll_type: str = "unroll", unroll_params: Optional[Dict] = None) -> int:
        """Store an equivalent circuit and link it to its representative."""
        # Create circuit record with representative_id pointing to original circuit
        circuit = CircuitRecord(
            id=None,
            width=width,
            gate_count=len(gates),
            gates=gates,
            permutation=permutation,
            representative_id=original_circuit_id  # Point to the representative
        )
        
        # Store the circuit
        circuit_id = self.store_circuit(circuit)
        
        # Link equivalent to representative in the equivalents table
        with sqlite3.connect(self.db_path) as conn:
            # Get the representative record for the original circuit
            cursor = conn.execute("""
                SELECT id FROM representatives 
                WHERE circuit_id = ?
            """, (original_circuit_id,))
            rep_row = cursor.fetchone()
            
            if rep_row:
                rep_id = rep_row[0]
                
                # Store the equivalent relationship
                conn.execute("""
                    INSERT OR IGNORE INTO equivalents (circuit_id, representative_id, unroll_type, unroll_params)
                    VALUES (?, ?, ?, ?)
                """, (circuit_id, rep_id, unroll_type, json.dumps(unroll_params) if unroll_params else None))
            
            conn.commit()
            
        return circuit_id

    def convert_circuit_to_equivalent(self, circuit_id: int, representative_id: int) -> bool:
        """Convert an existing circuit to be an equivalent of another circuit."""
        with sqlite3.connect(self.db_path) as conn:
            # First check if this conversion is valid
            cursor = conn.execute("SELECT id FROM circuits WHERE id = ?", (circuit_id,))
            if not cursor.fetchone():
                return False
                
            cursor = conn.execute("SELECT id FROM circuits WHERE id = ?", (representative_id,))
            if not cursor.fetchone():
                return False
            
            # Remove circuit from any existing representative relationships
            conn.execute("DELETE FROM representatives WHERE circuit_id = ?", (circuit_id,))
            
            # Add as equivalent to the representative
            conn.execute("""
                INSERT OR IGNORE INTO equivalents (circuit_id, representative_id, unroll_type)
                VALUES (?, ?, 'converted')
            """, (circuit_id, representative_id))
            
            conn.commit()
            return True

    def update_circuit_as_representative(self, circuit_id: int) -> bool:
        """Update a circuit to be marked as a representative for its gate composition."""
        try:
            # Get the circuit
            circuit = self.get_circuit(circuit_id)
            if not circuit:
                logger.error(f"Circuit {circuit_id} not found")
                return False
            
            # Calculate gate composition
            gate_composition = self._calculate_gate_composition(circuit.gates)
            
            # Get its dimension group
            dim_group_id = circuit.dim_group_id
            if not dim_group_id:
                logger.error(f"Circuit {circuit_id} not associated with a dimension group")
                return False
            
            with sqlite3.connect(self.db_path) as conn:
                # Set this circuit as its own representative
                conn.execute("""
                    UPDATE circuits 
                    SET representative_id = id 
                    WHERE id = ?
                """, (circuit_id,))
                
                # Check if a representative already exists for this composition
                cursor = conn.execute("""
                    SELECT r.id, r.circuit_id 
                    FROM representatives r
                    WHERE r.dim_group_id = ? AND r.gate_composition = ?
                """, (dim_group_id, json.dumps(gate_composition)))
                
                existing_rep = cursor.fetchone()
                
                if existing_rep:
                    existing_rep_id, existing_circuit_id = existing_rep
                    if existing_circuit_id != circuit_id:
                        # DISABLED: Don't automatically convert to equivalent - this causes sub-seeds to disappear
                        # Convert the current circuit to an equivalent of the existing representative
                        # logger.info(f"Circuit {circuit_id} converted to equivalent of representative {existing_circuit_id} (composition {gate_composition})")
                        # self.convert_circuit_to_equivalent(circuit_id, existing_rep_id)
                        logger.info(f"Circuit {circuit_id} could be converted to equivalent of representative {existing_circuit_id} (composition {gate_composition})")
                        return True
                    else:
                        logger.info(f"Circuit {circuit_id} is already the representative for composition {gate_composition}")
                        return True
                
                # If no existing representative, create a new representative record
                cursor = conn.execute("""
                    INSERT INTO representatives (dim_group_id, circuit_id, gate_composition, is_primary)
                    VALUES (?, ?, ?, ?)
                """, (dim_group_id, circuit_id, json.dumps(gate_composition), False))
                
                conn.commit()
                logger.info(f"Circuit {circuit_id} set as representative for composition {gate_composition}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating circuit {circuit_id} as representative: {e}")
            return False

    def _calculate_gate_composition(self, gates: List[Tuple]) -> Tuple[int, int, int]:
        """Calculate gate composition (NOT, CNOT, CCNOT counts)."""
        not_count = cnot_count = ccnot_count = 0
        
        for gate in gates:
            controls, target = gate
            control_count = len(controls)
            if control_count == 0:
                not_count += 1
            elif control_count == 1:
                cnot_count += 1
            elif control_count == 2:
                ccnot_count += 1
        
        return (not_count, cnot_count, ccnot_count)
    
    def cleanup_duplicate_representatives(self, dim_group_id: int) -> int:
        """Clean up duplicate representatives with the same gate composition."""
        with sqlite3.connect(self.db_path) as conn:
            # Find duplicate representatives (same dim_group_id and gate_composition)
            cursor = conn.execute("""
                SELECT gate_composition, COUNT(*) as count, GROUP_CONCAT(id) as rep_ids, GROUP_CONCAT(circuit_id) as circuit_ids
                FROM representatives 
                WHERE dim_group_id = ?
                GROUP BY gate_composition
                HAVING count > 1
            """, (dim_group_id,))
            
            duplicates_cleaned = 0
            
            for row in cursor.fetchall():
                gate_composition, count, rep_ids_str, circuit_ids_str = row
                rep_ids = [int(x) for x in rep_ids_str.split(',')]
                circuit_ids = [int(x) for x in circuit_ids_str.split(',')]
                
                # Keep the first representative, convert others to equivalents
                primary_rep_id = rep_ids[0]
                primary_circuit_id = circuit_ids[0]
                
                logger.info(f"Cleaning up {count} duplicate representatives for composition {gate_composition}")
                logger.info(f"Keeping representative {primary_rep_id} (circuit {primary_circuit_id})")
                
                for i in range(1, len(rep_ids)):
                    duplicate_rep_id = rep_ids[i]
                    duplicate_circuit_id = circuit_ids[i]
                    
                    # Convert duplicate circuit to equivalent
                    self.convert_circuit_to_equivalent(duplicate_circuit_id, primary_rep_id)
                    
                    # Remove duplicate representative entry
                    conn.execute("DELETE FROM representatives WHERE id = ?", (duplicate_rep_id,))
                    
                    logger.info(f"Converted representative {duplicate_rep_id} (circuit {duplicate_circuit_id}) to equivalent")
                    duplicates_cleaned += 1
            
            conn.commit()
            return duplicates_cleaned

    def mark_dim_group_processed(self, dim_group_id: int):
        """Mark a dimension group as fully processed."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE dim_groups SET is_processed = TRUE
                WHERE id = ?
            """, (dim_group_id,))
    
    def cleanup_representatives_after_unroll(self, dim_group_id: int, gate_composition: Tuple[int, int, int], 
                                           primary_representative_id: int, equivalent_circuits: List[List[Tuple]]) -> int:
        """
        Clean up representatives after unrolling by converting equivalent circuits to point to the primary representative.
        Returns the number of representatives that were converted to equivalents.
        """
        converted_count = 0
        
        with sqlite3.connect(self.db_path) as conn:
            # Get all representatives for this composition (excluding the primary one)
            cursor = conn.execute("""
                SELECT r.id, r.circuit_id, c.gates
                FROM representatives r
                JOIN circuits c ON r.circuit_id = c.id
                WHERE r.dim_group_id = ? AND r.gate_composition = ? AND r.circuit_id != ?
            """, (dim_group_id, json.dumps(gate_composition), primary_representative_id))
            
            other_representatives = cursor.fetchall()
            
            for rep_id, circuit_id, gates_json in other_representatives:
                circuit_gates = json.loads(gates_json)
                
                # Check if this circuit is equivalent to any of the unrolled circuits
                for equiv_gates in equivalent_circuits:
                    if self._gates_are_equivalent(circuit_gates, equiv_gates):
                        # Convert this representative to an equivalent
                        self.convert_circuit_to_equivalent(circuit_id, primary_representative_id)
                        
                        # Remove from representatives table
                        conn.execute("DELETE FROM representatives WHERE id = ?", (rep_id,))
                        
                        logger.info(f"Converted representative {circuit_id} to equivalent of {primary_representative_id}")
                        converted_count += 1
                        break
            
            conn.commit()
        
        return converted_count
    
    def _gates_are_equivalent(self, gates1: List[Tuple], gates2: List[Tuple]) -> bool:
        """Check if two gate sequences are exactly equivalent."""
        if len(gates1) != len(gates2):
            return False
        return gates1 == gates2
    
    def get_true_representatives_for_dim_group(self, dim_group_id: int) -> List[RepresentativeRecord]:
        """
        Get only true representatives (circuits where representative_id == circuit_id).
        This filters out circuits that have been converted to equivalents.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT r.id, r.dim_group_id, r.circuit_id, r.gate_composition, r.is_primary, r.fully_unrolled
                FROM representatives r
                JOIN circuits c ON r.circuit_id = c.id
                WHERE r.dim_group_id = ? AND c.representative_id = c.id
                ORDER BY r.gate_composition, r.circuit_id
            """, (dim_group_id,))
            
            return [
                RepresentativeRecord(
                    id=row[0],
                    dim_group_id=row[1],
                    circuit_id=row[2],
                    gate_composition=tuple(json.loads(row[3])),
                    is_primary=bool(row[4]),
                    fully_unrolled=bool(row[5])
                )
                for row in cursor.fetchall()
            ]
    
    def mark_representative_fully_unrolled(self, representative_id: int):
        """Mark a specific representative as fully unrolled."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE representatives SET fully_unrolled = TRUE
                WHERE id = ?
            """, (representative_id,))
            conn.commit()

    def get_all_dim_groups(self) -> List[DimGroupRecord]:
        """Get all dimension groups."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, width, gate_count, circuit_count, is_processed
                FROM dim_groups ORDER BY width, gate_count
            """)
            return [
                DimGroupRecord(
                    id=row[0], width=row[1], gate_count=row[2], 
                    circuit_count=row[3], is_processed=bool(row[4])
                )
                for row in cursor.fetchall()
            ]
    
    def get_unprocessed_dim_groups(self) -> List[DimGroupRecord]:
        """Get all dimension groups that have not been processed yet."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM dim_groups WHERE is_processed = 0")
            rows = cursor.fetchall()
            
            return [
                DimGroupRecord(
                    id=row[0],
                    width=row[1],
                    gate_count=row[2],
                    circuit_count=row[3],
                    is_processed=bool(row[4])
                ) for row in rows
            ]
    
    # Debris cancellation methods
    def store_debris_cancellation(self, debris_record: DebrisCancellationRecord) -> int:
        """Store debris cancellation analysis results."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO debris_cancellations 
                (circuit_id, dim_group_id, debris_gates, cancellation_path, non_triviality_score, 
                 final_gate_count, cancellation_metrics)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                debris_record.circuit_id,
                debris_record.dim_group_id,
                json.dumps(debris_record.debris_gates),
                json.dumps(debris_record.cancellation_path),
                debris_record.non_triviality_score,
                debris_record.final_gate_count,
                json.dumps(debris_record.cancellation_metrics)
            ))
            return cursor.lastrowid
    
    def get_debris_cancellation(self, circuit_id: int) -> Optional[DebrisCancellationRecord]:
        """Get debris cancellation analysis for a circuit."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, circuit_id, dim_group_id, debris_gates, cancellation_path, 
                       non_triviality_score, final_gate_count, cancellation_metrics
                FROM debris_cancellations WHERE circuit_id = ?
            """, (circuit_id,))
            row = cursor.fetchone()
            
            if row:
                return DebrisCancellationRecord(
                    id=row[0],
                    circuit_id=row[1],
                    dim_group_id=row[2],
                    debris_gates=json.loads(row[3]),
                    cancellation_path=json.loads(row[4]),
                    non_triviality_score=row[5],
                    final_gate_count=row[6],
                    cancellation_metrics=json.loads(row[7])
                )
            return None
    
    # Job queue methods
    def create_job(self, job: JobRecord) -> int:
        """Create a new job in the queue."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO jobs (job_type, status, priority, parameters)
                VALUES (?, ?, ?, ?)
            """, (
                job.job_type,
                job.status,
                job.priority,
                json.dumps(job.parameters)
            ))
            return cursor.lastrowid
    
    def get_pending_jobs(self, job_type: Optional[str] = None, limit: int = 10) -> List[JobRecord]:
        """Get pending jobs, optionally filtered by type."""
        with sqlite3.connect(self.db_path) as conn:
            if job_type:
                cursor = conn.execute("""
                    SELECT id, job_type, status, priority, parameters, result, error_message,
                           created_at, started_at, completed_at
                    FROM jobs WHERE status = 'pending' AND job_type = ?
                    ORDER BY priority DESC, created_at ASC LIMIT ?
                """, (job_type, limit))
            else:
                cursor = conn.execute("""
                    SELECT id, job_type, status, priority, parameters, result, error_message,
                           created_at, started_at, completed_at
                    FROM jobs WHERE status = 'pending'
                    ORDER BY priority DESC, created_at ASC LIMIT ?
                """, (limit,))
            
            return [
                JobRecord(
                    id=row[0], job_type=row[1], status=row[2], priority=row[3],
                    parameters=json.loads(row[4]), result=json.loads(row[5]) if row[5] else None,
                    error_message=row[6], created_at=row[7], started_at=row[8], completed_at=row[9]
                )
                for row in cursor.fetchall()
            ]
    
    def update_job_status(self, job_id: int, status: str, result: Optional[Dict] = None, 
                         error_message: Optional[str] = None):
        """Update job status and results."""
        with sqlite3.connect(self.db_path) as conn:
            if status == 'running':
                conn.execute("""
                    UPDATE jobs SET status = ?, started_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status, job_id))
            elif status in ['completed', 'failed']:
                conn.execute("""
                    UPDATE jobs SET status = ?, result = ?, error_message = ?, completed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status, json.dumps(result) if result else None, error_message, job_id))
            else:
                conn.execute("""
                    UPDATE jobs SET status = ? WHERE id = ?
                """, (status, job_id))
    
    # ML features methods
    def store_ml_features(self, ml_record: MLFeatureRecord) -> int:
        """Store ML features for a circuit."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO ml_features 
                (circuit_id, dim_group_id, features, complexity_prediction, optimization_suggestion)
                VALUES (?, ?, ?, ?, ?)
            """, (
                ml_record.circuit_id,
                ml_record.dim_group_id,
                json.dumps(ml_record.features),
                ml_record.complexity_prediction,
                ml_record.optimization_suggestion
            ))
            return cursor.lastrowid
    
    def get_ml_features(self, circuit_id: int) -> Optional[MLFeatureRecord]:
        """Get ML features for a circuit."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, circuit_id, dim_group_id, features, complexity_prediction, optimization_suggestion
                FROM ml_features WHERE circuit_id = ?
            """, (circuit_id,))
            row = cursor.fetchone()
            
            if row:
                return MLFeatureRecord(
                    id=row[0],
                    circuit_id=row[1],
                    dim_group_id=row[2],
                    features=json.loads(row[3]),
                    complexity_prediction=row[4],
                    optimization_suggestion=row[5]
                )
            return None
    
    # Statistics and analytics
    def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics."""
        with sqlite3.connect(self.db_path) as conn:
            stats = {}
            
            # Circuit counts
            cursor = conn.execute("SELECT COUNT(*) FROM circuits")
            stats['total_circuits'] = cursor.fetchone()[0]
            
            # Dim group counts
            cursor = conn.execute("SELECT COUNT(*) FROM dim_groups")
            stats['total_dim_groups'] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM dim_groups WHERE is_processed = TRUE")
            stats['processed_dim_groups'] = cursor.fetchone()[0]
            
            # Representative counts
            cursor = conn.execute("SELECT COUNT(*) FROM representatives")
            stats['total_representatives'] = cursor.fetchone()[0]
            
            # Equivalent counts
            cursor = conn.execute("SELECT COUNT(*) FROM equivalents")
            stats['total_equivalents'] = cursor.fetchone()[0]
            
            # Job counts
            cursor = conn.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status")
            stats['job_status_counts'] = dict(cursor.fetchall())
            
            # Debris cancellation counts
            cursor = conn.execute("SELECT COUNT(*) FROM debris_cancellations")
            stats['debris_cancellations'] = cursor.fetchone()[0]
            
            # ML features counts
            cursor = conn.execute("SELECT COUNT(*) FROM ml_features")
            stats['ml_features'] = cursor.fetchone()[0]
            
            return stats
    
    def store_simplification(self, original_id: int, simplified_id: int, 
                           target_dim_group_id: int, metrics: Dict[str, Any], 
                           simplification_type: str) -> int:
        """Store a simplification record."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO simplifications 
                (original_circuit_id, simplified_circuit_id, target_dim_group_id, 
                 reduction_metrics, simplification_type)
                VALUES (?, ?, ?, ?, ?)
            """, (
                original_id,
                simplified_id,
                target_dim_group_id,
                json.dumps(metrics),
                simplification_type
            ))
            return cursor.lastrowid

    def delete_circuit(self, circuit_id: int) -> bool:
        """Delete a circuit and its representative entry if it exists."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Delete from representatives table first (if exists)
                conn.execute("DELETE FROM representatives WHERE circuit_id = ?", (circuit_id,))
                
                # Delete from circuits table
                cursor = conn.execute("DELETE FROM circuits WHERE id = ?", (circuit_id,))
                
                # Return True if a circuit was actually deleted
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to delete circuit {circuit_id}: {e}")
            return False 
    
    def fix_circuit_dimension_group(self, circuit_id: int) -> bool:
        """Fix a circuit that's in the wrong dimension group."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get the circuit details
                cursor = conn.execute("""
                    SELECT width, gate_count, gates 
                    FROM circuits 
                    WHERE id = ?
                """, (circuit_id,))
                
                result = cursor.fetchone()
                if not result:
                    logger.error(f"Circuit {circuit_id} not found")
                    return False
                
                width, stored_gate_count, gates_json = result
                gates = json.loads(gates_json)
                actual_gate_count = len(gates)
                
                # Find or create the correct dimension group
                correct_dg = self.get_dim_group(width, actual_gate_count)
                if not correct_dg:
                    # Create new dimension group
                    new_dg = DimGroupRecord(
                        id=None, 
                        width=width, 
                        gate_count=actual_gate_count, 
                        circuit_count=0, 
                        is_processed=False
                    )
                    correct_dg_id = self.store_dim_group(new_dg)
                else:
                    correct_dg_id = correct_dg.id
                
                # Get the old dimension group ID
                old_cursor = conn.execute("SELECT dim_group_id FROM dim_group_circuits WHERE circuit_id = ?", (circuit_id,))
                old_result = old_cursor.fetchone()
                old_dg_id = old_result[0] if old_result else None
                
                # Update circuit's gate count if needed
                if stored_gate_count != actual_gate_count:
                    conn.execute("""
                        UPDATE circuits 
                        SET gate_count = ? 
                        WHERE id = ?
                    """, (actual_gate_count, circuit_id))
                
                # Remove from old dimension group
                if old_dg_id:
                    conn.execute("DELETE FROM dim_group_circuits WHERE dim_group_id = ? AND circuit_id = ?", 
                               (old_dg_id, circuit_id))
                
                # Add to correct dimension group
                conn.execute("""
                    INSERT OR IGNORE INTO dim_group_circuits (dim_group_id, circuit_id) 
                    VALUES (?, ?)
                """, (correct_dg_id, circuit_id))
                
                # Update representatives table
                conn.execute("""
                    UPDATE representatives 
                    SET dim_group_id = ? 
                    WHERE circuit_id = ?
                """, (correct_dg_id, circuit_id))
                
                conn.commit()
                logger.info(f"✅ Fixed circuit {circuit_id}: moved from dim group {old_dg_id} to {correct_dg_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to fix circuit {circuit_id} dimension group: {e}")
            return False