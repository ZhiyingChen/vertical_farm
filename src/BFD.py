

class Bin():
    """ Container for items that keeps a running sum """
    def __init__(self):
        self.items = []
        self.sum = 0

    def append(self, item):
        self.items.append(item)
        self.sum += item

    def __str__(self):
        """ Printable representation """
        return 'Bin(sum=%d, items=%s)' % (self.sum, str(self.items))


class Pack():
    def __init__(self, values, maxVal):
        self.values = values
        self.maxValue = maxVal

    def FFDPack(self):
        '''First fit decreasing pack'''
        values = sorted(self.values, reverse=True)
        maxValue = self.maxValue
        bins = []

        for item in values:
            # Try to fit item into a bin
            for bin in bins:
                if bin.sum + item <= maxValue:
                    # print 'Adding', item, 'to', bin
                    bin.append(item)
                    break
            else:
                # item didn't fit into any bin, start a new bin
                # print 'Making new bin for', item
                bin = Bin()
                bin.append(item)
                bins.append(bin)

        return bins

    def BFDPack(self):
        '''Best Fit Decreasing'''
        values = sorted(self.values, reverse=True)
        maxValue = self.maxValue
        bins = []

        for item in values:
            # Try to fit item into a bin

            n = len(bins)
            tightestInd = n
            leftMin = maxValue
            for i in range(n):

                try:
                    bin = bins[i]
                    if bin.sum + item <= maxValue:
                        left = maxValue - bin.sum - item
                        if left < leftMin:
                            tightestInd = i


                except IndexError:
                    bin = Bin()
                    bin.append(item)
                    bins.append(bin)
            try:
                bins[tightestInd].append(item)
            except IndexError:
                bin = Bin()
                bin.append(item)
                bins.append(bin)

        return bins
