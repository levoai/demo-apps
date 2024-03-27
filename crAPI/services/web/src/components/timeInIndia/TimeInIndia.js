import React, { useState, useEffect } from 'react';
import axios from 'axios';

const TimeInIndia = () => {
  const [time, setTime] = useState(null);

  useEffect(() => {
    const fetchTime = async () => {
      try {
        const response = await axios.get('http://worldtimeapi.org/api/timezone/Asia/Kolkata');
        setTime(response.data.datetime);
      } catch (error) {
        console.error('Error fetching time:', error);
      }
    };

    fetchTime();

    return () => {
      setTime(null);
    };
  }, []);

  return (
    <div>
      <h2>Current Time in India</h2>
      {time && <p>{time}</p>}
    </div>
  );
};

export default TimeInIndia;
