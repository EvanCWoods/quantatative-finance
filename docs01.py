from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
import datetime     # For datetime objects
import os.path      # To manage paths
import sys          # To find out the script name (in argv[0])
import backtrader as bt


class TestStrategy(bt.Strategy):

    def log(self, txt, dt=None):
        '''Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the close line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # Keep track of pending orders
        self.order = None
        self.buyprice = None
        self.buycomm = None

    # Print out the order status
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy / sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED: price %.2f, cost %.2f, commission %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm)
                )
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:
                self.log(
                    'SELL EXECUTED: price %.2f, cost %.2f, commission %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm)
                )
            self.bar_executed = len(self)

        elif order.status in [order.Cancelled, order.Margin, order.Rejected]:
            self.log('Order Cnaceled/margin/Rejected')

        # Write down: no opending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT:, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    # Open or close positions based on a set of parameters
    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if order is pending... if yes, we cannot send a 2nd
        if self.order:
            return

        # Check if we are in the market
        if not self.position:
            # Check if the previous 3 closes were higher than this close
            if self.dataclose[0] < self.dataclose[-1]:
                if self.dataclose[-1] < self.dataclose[-2]:
                    # If the conditions are met, buy
                    self.log('BUY CREATE, %.2f' % self.dataclose[0])
                    self.buy()
        else:
            # Already in the market
            if len(self) >= (self.bar_executed + 5):
                # Sell (with defualt parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()


if __name__ == '__main__':
    # Create the cerebro entity:
    cerebro = bt.Cerebro()

    # Add a strategy:
    cerebro.addstrategy(TestStrategy)

    # Datas are in a subfolder of the samples. Need to find where the script is -
    #  - Becuase it could have been called from anywhere
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, '../data/AAPL.csv')

    # Create data feed
    data = bt.feeds.YahooFinanceCSVData(
        dataname=datapath,
        # Do not pass values before this date:
        fromdate=datetime.datetime(2000, 1, 1),
        # Do not pass values after this date:
        todate=datetime.datetime(2000, 12, 31),
        reverse=False
    )

    # Add the data to cerebro:
    cerebro.adddata(data)

    # Set the starting balance of the portfolio
    cerebro.broker.setcash(100000.0)
    # Set the commission fee
    cerebro.broker.setcommission(commission=0.01)
    # Print out the starting balance
    print('Starting Portfolio Value: %.2f' % cerebro.broker.get_value())
    # Run over everything
    cerebro.run()
    # Print out the final balance
    print('Final portfolio value: %.2f' % cerebro.broker.get_value())


