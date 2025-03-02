import statistics

if __name__ == '__main__':
    measurement = {"type": "download",
                   "size": 10000000,
                   "servertime": 0.11599969900000001,
                   "fulltime": 0.8344790935516357,
                   "ttfb": 0.818069}

    measurement2 = {"type": "download",
                   "size": 10000000,
                   "servertime": 0.040999889000000005,
                   "fulltime": 0.5053019523620605,
                   "ttfb": 0.489929}

    measurements = []
    measurements.append(measurement)
    measurements.append(measurement2)



    latencies = [(m["ttfb"] - m["servertime"]) * 1e3 for m in measurements]
    jitter = statistics.median([abs(latencies[i] - latencies[i - 1]) for i in range(1, len(latencies))])

    latency = statistics.median(latencies)

    downspeed = statistics.median([(m["size"] * 8 / (m["fulltime"] - m["ttfb"])) / 1e6 for m in measurements])

    print("jitter:" + str(jitter))
    print("latency:" + str(latency))
    print("downspeed:" + str(downspeed))