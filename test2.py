import statistics

if __name__ == '__main__':
    s = "cfRequestDuration;dur=55.999994"
    a = float(s.split(',')[0].split('=')[1]) / 1e3
    print(a)