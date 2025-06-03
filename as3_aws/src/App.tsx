import React, { useState } from 'react';
import { 
  Container, 
  Paper, 
  Typography, 
  Box, 
  TextField, 
  Button,
  List,
  ListItem,
  ListItemText,
  Divider
} from '@mui/material';
import { useDropzone } from 'react-dropzone';

function App() {
  const [files, setFiles] = useState<File[]>([]);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<string[]>([]);

  const { getRootProps, getInputProps } = useDropzone({
    onDrop: (acceptedFiles) => {
      setFiles(prev => [...prev, ...acceptedFiles]);
    }
  });

  const handleQuerySubmit = async () => {
    // TODO: 实现查询逻辑
    setResults([`查询结果: ${query}`]);
  };

  const handleFileUpload = async () => {
    // TODO: 实现文件上传到S3的逻辑
    console.log('上传文件:', files);
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        文件查询系统
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          文件上传
        </Typography>
        <Box {...getRootProps()} 
          sx={{ 
            border: '2px dashed #ccc',
            borderRadius: 2,
            p: 3,
            mb: 2,
            textAlign: 'center',
            cursor: 'pointer'
          }}>
          <input {...getInputProps()} />
          <Typography>
            拖放文件到此处，或点击选择文件
          </Typography>
        </Box>
        {files.length > 0 && (
          <>
            <List>
              {files.map((file, index) => (
                <ListItem key={index}>
                  <ListItemText primary={file.name} secondary={`${(file.size / 1024).toFixed(2)} KB`} />
                </ListItem>
              ))}
            </List>
            <Button 
              variant="contained" 
              onClick={handleFileUpload}
              fullWidth
            >
              上传文件
            </Button>
          </>
        )}
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          查询
        </Typography>
        <TextField
          fullWidth
          label="输入查询内容"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          sx={{ mb: 2 }}
        />
        <Button 
          variant="contained" 
          onClick={handleQuerySubmit}
          fullWidth
        >
          提交查询
        </Button>

        {results.length > 0 && (
          <Box sx={{ mt: 3 }}>
            <Divider sx={{ mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              查询结果
            </Typography>
            <List>
              {results.map((result, index) => (
                <ListItem key={index}>
                  <ListItemText primary={result} />
                </ListItem>
              ))}
            </List>
          </Box>
        )}
      </Paper>
    </Container>
  );
}

export default App; 