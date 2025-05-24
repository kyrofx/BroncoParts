import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Tree from 'react-d3-tree';
import api from '../services/api';
import { Box, CircularProgress, Alert, Button, Typography, Paper } from '@mui/material';

const ProjectTreeView = () => {
    const { projectId } = useParams();
    const navigate = useNavigate();
    const [treeData, setTreeData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [project, setProject] = useState(null);

    const fetchProjectDetails = useCallback(async () => {
        try {
            const response = await api.get(`/projects/${projectId}`);
            setProject(response.data.project);
        } catch (err) {
            console.error("Failed to fetch project details for tree view:", err);
            // Not setting top-level error here, as the main focus is the tree
        }
    }, [projectId]);

    const fetchTreeData = useCallback(async () => {
        try {
            setLoading(true);
            const response = await api.get(`/projects/${projectId}/tree`);
            // Assuming the API returns data in a format suitable for react-d3-tree
            // e.g., { name: 'Project Root', children: [ { name: 'Assembly 1', children: [...] }, { name: 'Part 1'} ] }
            setTreeData(response.data); // Adjust if the API nests the tree data differently
            setError('');
        } catch (err) {
            setError('Failed to fetch project tree data. ' + (err.response?.data?.message || err.message));
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, [projectId]);

    useEffect(() => {
        fetchProjectDetails();
        fetchTreeData();
    }, [fetchProjectDetails, fetchTreeData]);

    const handleNodeClick = useCallback((nodeData) => {
        // nodeData.data contains the original node attributes from your data structure
        if (nodeData.data && nodeData.data.id) {
            const type = nodeData.data.type || 'part'; // Default to 'part' if type is not specified
            if (type.toLowerCase() === 'assembly') {
                navigate(`/assemblies/${nodeData.data.id}`);
            } else {
                navigate(`/parts/${nodeData.data.id}`);
            }
        }
    }, [navigate]);
    
    // Custom styles for the tree nodes to make them more readable
    const foreignObjectProps = { width: 200, height: 100, x: -100, y: -25 };
    const renderForeignObjectNode = ({
        nodeDatum,
        toggleNode,
        foreignObjectProps: foreignObjectPropsInternal
      }) => (
        <g>
          {/* `foreignObject` requires width & height to be explicitly set. */}
          <foreignObject {...foreignObjectPropsInternal}>
            <Box 
                sx={{ 
                    border: '1px solid lightgray', 
                    borderRadius: '4px', 
                    p: 1, 
                    backgroundColor: 'white',
                    textAlign: 'center',
                    cursor: 'pointer'
                }}
                onClick={toggleNode} // Allow expanding/collapsing by clicking the node
            >
              <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>{nodeDatum.name}</Typography>
              {nodeDatum.attributes?.part_number && (
                <Typography variant="caption">PN: {nodeDatum.attributes.part_number}</Typography>
              )}
              {/* Add more details as needed */}
            </Box>
          </foreignObject>
        </g>
      );


    if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 'calc(100vh - 64px)' }}><CircularProgress /></Box>;
    if (error) return <Alert severity="error" sx={{ m: 2 }}>{error}</Alert>;
    if (!treeData) return <Alert severity="info" sx={{ m: 2 }}>No tree data available for this project.</Alert>;

    return (
        <Box sx={{ width: '100%', height: 'calc(100vh - 128px)', p: 2, display: 'flex', flexDirection: 'column' }}>
            <Paper elevation={3} sx={{ p: 2, mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="h5" component="h1">
                        {project ? `${project.name} - Tree View` : 'Project Tree View'}
                    </Typography>
                    <Button variant="outlined" onClick={() => navigate(`/projects/${projectId}`)}>
                        Back to Project Details
                    </Button>
                </Box>
            </Paper>
            <Box sx={{ flexGrow: 1, border: '1px solid #ddd', borderRadius: '4px', backgroundColor: '#f9f9f9' }}>
                <Tree
                    data={treeData}
                    orientation="vertical"
                    pathFunc="diagonal"
                    collapsible={true}
                    zoomable={true}
                    translate={{ x: 200, y: 50 }} // Initial translation to center the tree
                    scaleExtent={{ min: 0.1, max: 2 }}
                    nodeSize={{ x: 250, y: 150 }} // Increased spacing between nodes
                    separation={{ siblings: 1.5, nonSiblings: 2 }}
                    onNodeClick={handleNodeClick} // Use the memoized handler
                    renderCustomNodeElement={(rd3tProps) =>
                        renderForeignObjectNode({ ...rd3tProps, foreignObjectProps })
                    }
                    svgClassName="project-tree-svg" // For potential global CSS overrides
                    rootNodeClassName="project-tree-root-node"
                    branchNodeClassName="project-tree-branch-node"
                    leafNodeClassName="project-tree-leaf-node"
                />
            </Box>
        </Box>
    );
};

export default ProjectTreeView;
