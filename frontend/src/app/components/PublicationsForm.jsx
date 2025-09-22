const handleFileUpload = (event) => {
  const uploadedFiles = Array.from(event.target.files);
  
  const newFiles = uploadedFiles.map(file => ({
    file: file, // Keep the actual File object
    name: file.name,
    size: file.size,
    type: file.type,
    lastModified: file.lastModified,
    url: URL.createObjectURL(file),
    metadata: {
      title: '',
      author: '',
      year: '',
      doi: '',
      abstract: ''
    }
  }));

  setFiles(prevFiles => [...prevFiles, ...newFiles]);
  
  // Update parent component with new files
  updateFormData({
    publicationType,
    files: [...files, ...newFiles]
  });
};

// Add cleanup for blob URLs when files are removed
const handleRemoveFile = (index) => {
  setFiles(prevFiles => {
    const newFiles = [...prevFiles];
    // Revoke the blob URL to prevent memory leaks
    if (newFiles[index].url.startsWith('blob:')) {
      URL.revokeObjectURL(newFiles[index].url);
    }
    newFiles.splice(index, 1);
    return newFiles;
  });

  // Update parent component
  updateFormData({
    publicationType,
    files: files.filter((_, i) => i !== index)
  });
};

const identifiers = [
  { value: 'journal', label: 'Journal', disabled: false },
  { value: 'conference', label: 'Conference', disabled: false },
  { value: 'book', label: 'Book', disabled: false },
  { value: 'bookChapter', label: 'Book Chapter', disabled: false },
  { value: 'article', label: 'Article', disabled: false },
  { value: 'thesis', label: 'Thesis', disabled: false },
  { value: 'report', label: 'Report', disabled: false },
  { value: 'webPage', label: 'Web Page', disabled: false },
  { value: 'other', label: 'Other', disabled: false }
];

const PublicationTypeSelector = () => {
  const [publicationType, setPublicationType] = useState('');

  const handleChange = (event) => {
    setPublicationType(event.target.value);
  };

  return (
    <FormControl fullWidth>
      <InputLabel id="publication-type-label">Publication Type</InputLabel>
      <Select
        labelId="publication-type-label"
        id="publication-type"
        value={publicationType}
        label="Publication Type"
        onChange={handleChange}
      >
        {identifiers.map((type) => (
          <MenuItem 
            key={type.value} 
            value={type.value}
            disabled={type.disabled}
            sx={{
              '&.Mui-disabled': {
                opacity: 0.6,
                color: 'text.disabled'
              }
            }}
          >
            {type.label}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
};

export default PublicationTypeSelector; 