# Use an official Node.js runtime as a parent image
FROM node:18-alpine

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy package.json and package-lock.json to the working directory
COPY package*.json ./

RUN echo "--- Contents before npm install ---" && ls -la

# Install any needed packages with maximum verbosity
RUN npm install --verbose

RUN echo "--- Contents after npm install ---" && ls -la

# Copy the application source code
COPY src ./src

# Make port 3000 available to the world outside this container
EXPOSE 3000

# Define the command to run your app
CMD ["node", "src/index.js"]
