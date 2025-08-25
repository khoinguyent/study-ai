// Simple test to debug the issue
console.log('Testing basic Node.js functionality...');

try {
  // Test basic imports
  const fs = require('fs');
  console.log('fs module loaded successfully');
  
  // Test if dist folder exists
  if (fs.existsSync('./dist')) {
    console.log('dist folder exists');
    const files = fs.readdirSync('./dist');
    console.log('dist folder contents:', files);
  } else {
    console.log('dist folder does not exist');
  }
  
  // Test if we can read the built index.js
  if (fs.existsSync('./dist/index.js')) {
    console.log('index.js exists, trying to read it...');
    const content = fs.readFileSync('./dist/index.js', 'utf8');
    console.log('index.js first 200 chars:', content.substring(0, 200));
  } else {
    console.log('index.js does not exist');
  }
  
} catch (error) {
  console.error('Error:', error.message);
  console.error('Stack:', error.stack);
}
