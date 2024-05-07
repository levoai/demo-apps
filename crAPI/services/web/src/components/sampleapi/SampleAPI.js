import React, { useState, useEffect } from 'react';
import axios from 'axios';

const SampleAPI = () => {
  const [time, setTime] = useState(null);

  useEffect(() => {
    const fetchTime = async () => {
      try {
        const response = await axios.get('https://reqres.in/api/users?token=sometoken?');
      } catch (error) {
        console.error('Error fetching sample API:', error);
      }
    };

    fetchTime();

    return () => {
      setTime(null);
    };
  }, []);

  return (
    <div>
    </div>
  );
};

export default SampleAPI;
