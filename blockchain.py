"""
In this assignment you will extend and implement a class framework to create a simple but functional blockchain that combines the ideas of proof-of-work, transactions, blocks, and blockchains.
You may create new member functions, but DO NOT MODIFY any existing APIs.  These are the interface into your blockchain.


This blockchain has the following consensus rules (it is a little different from Bitcoin to make testing easier):

Blockchain

1. There are no consensus rules pertaining to the minimum proof-of-work of any blocks.  That is it has no "difficulty adjustment algorithm".
Instead, your code will be expected to properly place blocks of different difficulty into the correct place in the blockchain and discover the most-work tip.

2. A block with no transactions (no coinbase) is valid (this will help us isolate tests).

3. If a block as > 0 transactions, the first transaction MUST be the coinbase transaction.

Block Merkle Tree

1. You must use sha256 hash 
2. You must use 0 if additional items are needed to pad odd merkle levels
(more specific information is included below)

Transactions

1. A transaction with inputs==None is a valid mint (coinbase) transaction.  The coins created must not exceed the per-block "minting" maximum.

2. If the transaction is not a coinbase transaction, coins cannot be created.  In other words, coins spent (inputs) must be >= coins sent (outputs).

3. Constraint scripts (permission to spend) are implemented via python lambda expressions (anonymous functions).  These constraint scripts must accept a list of parameters, and return True if
   permission to spend is granted.  If execution of the constraint script throws an exception or returns anything except True do not allow spending!

461: You may assume that every submitted transaction is correct.
     This means that you should just make the Transaction validate() function return True
     You do not need to worry about tracking the UTXO (unspent transaction outputs) set.

661: You need to verify transactions, their constraint and satisfier scripts, and track the UTXO set.


Some useful library functions:

Read about hashlib.sha256() to do sha256 hashing in python.
Convert the sha256 array of bytes to a big endian integer via: int.from_bytes(bunchOfBytes,"big")

Read about the "dill" library to serialize objects automatically (dill.dumps()).  "Dill" is like "pickle", but it can serialize python lambda functions, which you need to install via "pip3 install dill".  The autograder has this library pre-installed.
You'll probably need this when calculating a transaction id.

"""
import sys
assert sys.version_info >= (3, 6)
import hashlib
import pdb
import copy
import json
# pip3 install dill
import dill as serializer
from collections import deque

class Output:
    """ This models a transaction output """
    def __init__(self, constraint = None, amount = 0):
        """ constraint is a function that takes 1 argument which is a list of 
            objects and returns True if the output can be spent.  For example:
            Allow spending without any constraints (the "satisfier" in the Input object can be anything)
            lambda x: True

            Allow spending if the spender can add to 100 (example: satisfier = [40,60]):
            lambda x: x[0] + x[1] == 100

            If the constraint function throws an exception, do not allow spending.
            For example, if the satisfier = ["a","b"] was passed to the previous constraint script

            If the constraint is None, then allow spending without constraint

            amount is the quantity of tokens associated with this output """
        self.constraint = constraint
        self.amount = amount

class Input:
    """ This models an input (what is being spent) to a blockchain transaction """
    def __init__(self, txHash, txIdx, satisfier):
        """ This input references a prior output by txHash and txIdx.
            txHash is therefore the prior transaction hash
            txIdx identifies which output in that prior transaction is being spent.  It is a 0-based index.
            satisfier is a list of objects that is be passed to the Output constraint script to prove that the output is spendable.
        """
        self.hash = txHash
        self.txIdx = txIdx
        self.satisfier = satisfier
    

class Transaction:
    """ This is a blockchain transaction """
    def __init__(self, inputs=None, outputs=None, data = None):
        """ Initialize a transaction from the provided parameters.
            inputs is a list of Input objects that refer to unspent outputs.
            outputs is a list of Output objects.
            data is a byte array to let the transaction creator put some 
              arbitrary info in their transaction.
        """
        self.inputs = inputs
        self.outputs = outputs
        self.data = data
        pass

    def getHash(self):
        """Return this transaction's probabilistically unique identifier as a big-endian integer"""
        inputHash = ""
        outputHash = ""
        if self.inputs:
            for i in self.inputs:
                inputHash += i.hash

        
        inputsOutputs = hashlib.sha256(inputHash) + hashlib.sha256(outputHash) + self.data
        return hashlib.sha256(inputsOutputs)

    def getInputs(self):
        """ return a list of all inputs that are being spent """
        return self.inputs

    def getOutput(self, n):
        """ Return the output at a particular index """
        return self.outputs[n]

    def validateMint(self, maxCoinsToCreate):
        """ Validate a mint (coin creation) transaction.
            A coin creation transaction should have no inputs,
            and the sum of the coins it creates must be less than maxCoinsToCreate.
        """
        total_coins = 0
        for out in self.outputs:
            total_coins += out.amount
        
        # no inputs and coins it creates less than maxCoinsToCreate
        return not self.inputs and total_coins <= maxCoinsToCreate

    def validate(self, unspentOutputDict):
        """ Validate this transaction given a dictionary of unspent transaction outputs.
            unspentOutputDict is a dictionary of items of the following format: { (txHash, offset) : Output }
            offset helps us identify the exact output
        """
        # if you are taking 461: return True
    
        return True


class HashableMerkleTree:
    """ A merkle tree of hashable objects.

        If no transaction or leaf exists, use 32 bytes of 0.
        The list of objects that are passed must have a member function named
        .getHash() that returns the object's sha256 hash as an big endian integer.

        Your merkle tree must use sha256 as your hash algorithm and big endian
        conversion to integers so that the tree root is the same for everybody.
        This will make it easy to test.

        If a level has an odd number of elements, append a 0 value element.
        if the merkle tree has no elements, return 0.

    """

    def __init__(self, hashableList = None):
        self.hashableList = hashableList

    def _findMerkelHash(self,arr):
        if arr == None:
            return b'\x00' * 32 
        if len(arr) == 1:
            return arr[0]
        if len(arr) != 1 and len(arr) % 2 != 0:
            # check at each layer if it is odd and add zero to make it even
            arr.append(0)
        returnArr = []
        print("arr",arr)
        for i in range(0, len(arr), 2):
            first,second = arr[i], arr[i+1]
            if first == 0:
                first = b'\x00' * 32 
            else:
                first = first.getHash()
            if second == 0:
                second = b'\x00' * 32 
            else:
                second = second.getHash()

            combined = hashlib.sha256(first,second).digest()
            returnArr.append(combined)
        return self._findMerkelHash(returnArr)

    def calcMerkleRoot(self):
        """ Calculate the merkle root of this tree."""
        return int.from_bytes(self._findMerkelHash(self.hashableList),"big")


class BlockContents:
    """ The contents of the block (merkle tree of transactions)
        This class isn't really needed.  I added it so the project could be cut into
        just the blockchain logic, and the blockchain + transaction logic.
    """
    def __init__(self):
        self.data = HashableMerkleTree()

    def setData(self, d):
        self.data = d

    def getData(self):
        return self.data

    def calcMerkleRoot(self):
        return self.data.calcMerkleRoot()

class Block:
    """ This class should represent a blockchain block.
        It should have the normal fields needed in a block and also an instance of "BlockContents"
        where we will store a merkle tree of transactions.
    """
    def __init__(self,target=None,header=None,transactions=None,children=None, parent=None):
        # Hint, beyond the normal block header fields what extra data can you keep track of per block to make implementing other APIs easier?
        self.txs = transactions
        self.prevBlockHash = None
        self.nonce = 0
        self.target = target
        self.header = header
        self.BlockContents = BlockContents()
        self.parent = parent
        self.children = [] if not children else children
    def getContents(self):
        """ Return the Block content (a BlockContents object)"""
        return self.BlockContents.getData()

    def setContents(self, data):
        """ set the contents of this block's merkle tree to the list of objects in the data parameter """
        self.BlockContents.setData(data)

    def setTarget(self, target):
        """ Set the difficulty target of this block """
        self.target = target

    def getTarget(self):
        """ Return the difficulty target of this block """
        return self.target

    def getHash(self):
        """ Calculate the hash of this block. Return as an integer """
        txsHash = b""
        if self.txs:
            for t in self.txs:
                txsHash += t.getHash()
        nonceHash = hashlib.sha256(str(self.nonce).encode()).digest()
        targetHash = hashlib.sha256(str(self.target).encode()).digest()
        merkleRoot = self.BlockContents.calcMerkleRoot().to_bytes(32, 'big')  
        parentHash = self.parent.to_bytes(32, 'big')  
        concatenatedHash = txsHash + nonceHash + targetHash + merkleRoot + parentHash
        return int.from_bytes(hashlib.sha256(concatenatedHash),"big")
        
  

    def setPriorBlockHash(self, priorHash):
        """ Assign the parent block hash """
        self.prevBlockHash = priorHash

    def getPriorBlockHash(self):
        """ Return the parent block hash """
        return self.prevBlockHash 

    def mine(self,tgt):
        """Update the block header to the passed target (tgt) and then search for a nonce which produces a block who's hash is less than the passed target, "solving" the block"""
        self.header = tgt
        while self.getHash() <= tgt:
            self.nonce += 1

    def validate(self, unspentOutputs, maxMint):
        """ Given a dictionary of unspent outputs, and the maximum amount of
            coins that this block can create, determine whether this block is valid.
            Valid blocks satisfy the POW puzzle, have a valid coinbase tx, and have valid transactions (if any exist).

            Return None if the block is invalid.

            Return something else if the block is valid

            661 hint: you may want to return a new unspent output object (UTXO set) with the transactions in this
            block applied, for your own use when implementing other APIs.

            461: you can ignore the unspentOutputs field (just pass {} when calling this function)
        """
        assert type(unspentOutputs) == dict, "unspent outputs (unspent outputs) needs to be a dictionary of tuples (hash, index) -> Output"
        pass


class Blockchain(object):

    def __init__(self, genesisTarget, maxMintCoinsPerTx):
        """ Initialize a new blockchain and create a genesis block.
            genesisTarget is the difficulty target of the genesis block (that you should create as part of this initialization).
            maxMintCoinsPerTx is a consensus parameter -- don't let any block into the chain that creates more coins than this!
        """
        self.genesisBlock = Block(genesisTarget,None,None,None,None)
        self.maxMintCoinsPerTx = maxMintCoinsPerTx
        self.longestPowChain= self.genesisBlock
        self.forksTips = []

    def _bsfGetTip(self,startNode):
        q = deque()
        q.append(startNode)
        seen = set()
        maxNode = (0,None)
        currDepth = 0
        while q:
            for i in range(len(q)):
                curr = q.popleft()
                if len(curr.children) == 0:
                    # we are at one of the possible tips
                    if currDepth + 1 > maxNode[0]:
                        maxNode = [currDepth + 1, curr]
                for c in curr.children:
                    if c not in seen:
                        seen.add(c)
                        q.append(c)
            currDepth += 1
        return maxNode[1]

    def getTip(self):
        """ Return the block at the tip (end) of the blockchain fork that has the largest amount of work"""
        return self._bsfGetTip(self.genesisBlock)

    def getWork(self, target):
        """Get the "work" needed for this target.  Work is the ratio of the genesis target to the passed target"""
        return target/self.genesisBlock.getTarget()

    def _bfsWork(self,startBlock,targetHash):
        q = deque()
        q.append(startBlock)
        seen = set()
        currWork = 0
        while q:
            for i in range(len(q)):
                curr = q.popleft()
                for c in curr.children:
                    if c not in seen:
                        if c.getHash() == targetHash:
                            return currWork + 1
                        seen.add(c)
                        q.append(c)
            currWork += 1
        return None
    
    def getCumulativeWork(self, blkHash):
        """Return the cumulative work for the block identified by the passed hash.  Return None if the block is not in the blockchain"""
        self._bfsWork(self.genesisBlock,blkHash)

    
    def _bfsHeight(self,startNode,targetHeight):
        q = deque()
        q.append(startNode)
        seen = set()
        currHeight = 0
        while q:
            for i in range(len(q)):
                curr = q.popleft()
                blocksAtHeight = []
                for c in curr.children:
                    if c not in seen:
                        seen.add(c)
                        blocksAtHeight.append(c)
                        q.append(c)
                if currHeight == targetHeight:
                    return blocksAtHeight
            currHeight += 1
        return []

    def getBlocksAtHeight(self, height):
        """Return an array of all blocks in the blockchain at the passed height (including all forks)"""
        return self._bfsHeight(self.genesisBlock,height)

    def extend(self, block):
        """Adds this block into the blockchain in the proper location, if it is valid.  The "proper location" may not be the tip!

           Hint: Note that this means that you must validate transactions for a block that forks off of any position in the blockchain.
           The easiest way to do this is to remember the UTXO set state for every block, not just the tip.
           For space efficiency "real" blockchains only retain a single UTXO state (the tip).  This means that during a blockchain reorganization
           they must travel backwards up the fork to the common block, "undoing" all transaction state changes to the UTXO, and then back down
           the new fork.  For this assignment, don't implement this detail, just retain the UTXO state for every block
           so you can easily "hop" between tips.

           Return false if the block is invalid (breaks any miner constraints), and do not add it to the blockchain."""
        pass


# --------------------------------------------
# You should make a bunch of your own tests before wasting time submitting stuff to gradescope.
# Its a LOT faster to test locally.  Try to write a test for every API and think about weird cases.

# Let me get you started:
def Test():
    # test creating blocks, mining them, and verify that mining with a lower target results in a lower hash
    b1 = Block()
    b1.mine(int("F"*64,16))
    h1 = b1.getHash()
    b2 = Block()
    b2.mine(int("F"*63,16))
    h2 = b2.getHash()
    assert h2 < h1

    t0 = Transaction(None, [Output(lambda x: True, 100)])
    # Negative test: minted too many coins
    assert t0.validateMint(50) == False, "1 output: tx minted too many coins"
    # Positive test: minted the right number of coins
    assert t0.validateMint(100) == True, "1 output: tx minted the right number of coins"

    class GivesHash:
        def __init__(self, hash):
            self.hash = hash
        def getHash(self):
            return self.hash

    assert HashableMerkleTree([GivesHash(x) for x in [106874969902263813231722716312951672277654786095989753245644957127312510061509]]).calcMerkleRoot().to_bytes(32,"big").hex() == "ec4916dd28fc4c10d78e287ca5d9cc51ee1ae73cbfde08c6b37324cbfaac8bc5"

    assert HashableMerkleTree([GivesHash(x) for x in [106874969902263813231722716312951672277654786095989753245644957127312510061509, 66221123338548294768926909213040317907064779196821799240800307624498097778386, 98188062817386391176748233602659695679763360599522475501622752979264247167302]]).calcMerkleRoot().to_bytes(32,"big").hex() == "ea670d796aa1f950025c4d9e7caf6b92a5c56ebeb37b95b072ca92bc99011c20"

    print ("yay local tests passed")

Test()
