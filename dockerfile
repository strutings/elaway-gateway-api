# Use the official Node.js image as a base image
FROM node:20.11.0

# Set the working directory inside the container
WORKDIR /app

# Copy the package.json and package-lock.json files to the working directory
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code to the working directory
COPY . .

# Build the TypeScript project
RUN npm run build

# Expose port 3000
EXPOSE 3000

# Command to run the application
CMD ["node", "dist/src/main.js"]
